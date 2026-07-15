"""Factored Chain-of-Verification (CoVe paper §3): baseline -> plan -> execute FACTORED -> revise.
Key invariant: verification answers NEVER see the baseline (prevents hallucination copy-through;
factored/factor+revise beat joint on every benchmark — Tables 1-3)."""
from __future__ import annotations
from pydantic import BaseModel, Field
from ..core.agent import Agent


class VerificationPlan(BaseModel):
    questions: list[str] = Field(min_length=1)


class VerificationAnswer(BaseModel):
    question: str
    answer: str


class CrossCheck(BaseModel):
    consistent: bool
    inconsistencies: list[str] = Field(default_factory=list)


class CoVeResult(BaseModel):
    baseline: str
    questions: list[str]
    answers: list[VerificationAnswer]
    inconsistencies: list[str]
    revised: str


class RevisedResponse(BaseModel):
    text: str


def run_cove(agent: Agent, query: str) -> CoVeResult:
    # 1. baseline
    baseline = agent.run(query, RevisedResponse).text
    # 2. plan verifications (conditions on baseline — allowed per paper)
    plan = agent.run(
        f"QUERY: {query}\nDRAFT: {baseline}\n"
        "List independent verification questions that fact-check every claim in the draft.",
        VerificationPlan)
    # 3. execute FACTORED — fresh context per question, baseline excluded (paper §3.3)
    answers = [VerificationAnswer(question=q,
                                  answer=agent.run(q, RevisedResponse).text)
               for q in plan.questions]
    # 4. factor+revise cross-check (paper Fig.3: explicit inconsistency detection wins)
    qa = "\n".join(f"Q: {a.question}\nA: {a.answer}" for a in answers)
    check = agent.run(
        f"DRAFT: {baseline}\nFrom another source:\n{qa}\n"
        "Identify inconsistencies between the draft and these independently sourced answers.",
        CrossCheck)
    revised = baseline if check.consistent else agent.run(
        f"QUERY: {query}\nDRAFT: {baseline}\nVERIFIED FACTS:\n{qa}\n"
        f"INCONSISTENCIES: {'; '.join(check.inconsistencies)}\n"
        "Rewrite the draft keeping only facts consistent with the verified answers.",
        RevisedResponse).text
    return CoVeResult(baseline=baseline, questions=plan.questions, answers=answers,
                      inconsistencies=check.inconsistencies, revised=revised)
