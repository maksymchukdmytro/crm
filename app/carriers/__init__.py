from .base import Carrier, CarrierError, ShipmentResult, TrackResult
from .meest import Meest
from .novaposhta import NovaPoshta
from .ukrposhta import Ukrposhta

CARRIERS: dict[str, type[Carrier]] = {
    NovaPoshta.code: NovaPoshta,
    Ukrposhta.code: Ukrposhta,
    Meest.code: Meest,
}


def get_carrier(code: str, settings: dict[str, str]) -> Carrier | None:
    cls = CARRIERS.get(code)
    return cls(settings) if cls else None


__all__ = ["CARRIERS", "Carrier", "CarrierError", "ShipmentResult", "TrackResult", "get_carrier"]
