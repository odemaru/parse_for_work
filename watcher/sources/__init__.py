from . import lamoda, magnit, mts, severstal, tbank, wildberries, x5

REGISTRY = {
    module.NAME: module
    for module in (wildberries, x5, mts, magnit, tbank, lamoda, severstal)
}
