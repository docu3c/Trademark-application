from pydantic import BaseModel, Field
from typing import List, Union


class TrademarkDetails(BaseModel):
    trademark_name: str = Field(
        description="The name of the Trademark", example="DISCOVER"
    )
    status: str = Field(description="The Status of the Trademark", example="Registered")
    serial_number: str = Field(
        description="The Serial Number of the trademark from Chronology section",
        example="87−693,628",
    )
    international_class_number: List[int] = Field(
        description="The International class number or Nice Classes number of the trademark from Goods/Services section or Nice Classes section",
        example=[18],
    )
    owner: str = Field(
        description="The owner of the trademark", example="WALMART STORES INC"
    )
    goods_services: str = Field(
        description="The goods/services from the document",
        example="LUGGAGE AND CARRYING BAGS; SUITCASES, TRUNKS, TRAVELLING BAGS, SLING BAGS FOR CARRYING INFANTS, SCHOOL BAGS; PURSES; WALLETS; RETAIL AND ONLINE RETAIL SERVICES",
    )
    page_number: int = Field(
        description="The page number where the trademark details are found in the document",
        example=3,
    )
    registration_number: Union[str, None] = Field(
        description="The Registration number of the trademark from Chronology section",
        example="5,809,957",
    )
    design_phrase: str = Field(
        description="The design phrase of the trademark",
        example="THE MARK CONSISTS OF THE STYLIZED WORD 'MINI' FOLLOWED BY 'BY MOTHERHOOD.'",
        default="",
    )
