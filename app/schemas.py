from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SuggestVendorsRequest(BaseModel):
    query_text: str
    location_precision: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    manual_area: Optional[str] = None
    client_platform: Optional[str] = None


class SuggestVendorsResponse(BaseModel):
    suggestions: List[Dict[str, Any]]
    generated_at: str
    source: str = "deterministic"


class InstructionPackPreset(BaseModel):
    restaurant_name: str
    menu_items: List[str] = Field(default_factory=list)
    app_name: str
    order_url: Optional[str] = None


class InstructionPackRequest(BaseModel):
    verbal_handover_notes: Optional[str] = None
    has_reference_photo: bool = False
    reference_photo_artifact_id: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    location_label: Optional[str] = None
    presets: List[InstructionPackPreset] = Field(default_factory=list)
    donor_display_name: Optional[str] = None
    seeker_display_name: Optional[str] = None
    user_id: Optional[str] = None


class InstructionPackResponse(BaseModel):
    pack_id: str
    delivery_instructions: str
    generated_at: str
    source: str
    donor_display_name: Optional[str] = None
    seeker_display_name: Optional[str] = None
    secure_photo_url: Optional[str] = None
