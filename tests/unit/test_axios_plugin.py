import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec

def test_axios_generator_content():
    gen = get_generator("axios-client")
    module = ModuleSpec(name="axiosmod")
    out = gen.generate(module)
    assert "axiosmod-axios.ts" in out
    content = out["axiosmod-axios.ts"]
    assert 'import axios from "axios";' in content
    assert "export class AxiosClient" in content
    assert "return axios({ method, url: this.baseUrl + url, data });" in content
