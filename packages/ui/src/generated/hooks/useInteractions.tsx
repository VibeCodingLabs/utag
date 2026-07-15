// generated from design.yaml interactions — do not edit by hand
import React from "react";

type Selections = Record<string, unknown>;

const SelectionContext = React.createContext<{
  selections: Selections;
  select: (key: string, value: unknown) => void;
}>({ selections: {}, select: () => undefined });

export function SelectionProvider({ children }: { children?: React.ReactNode }) {
  const [selections, setSelections] = React.useState<Selections>({});
  const select = (key: string, value: unknown) =>
    setSelections((prev) => ({ ...prev, [key]: value }));
  return (
    <SelectionContext.Provider value={{ selections, select }}>
      {children}
    </SelectionContext.Provider>
  );
}

export function useSelect(): (key: string, value: unknown) => void {
  return React.useContext(SelectionContext).select;
}

export function useSelected(key: string): unknown {
  return React.useContext(SelectionContext).selections[key];
}
