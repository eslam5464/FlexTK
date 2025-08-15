from typing import Optional

from lib.schemas.base import BaseSchema
from pydantic import Field
from stripe import Customer


class CustomerCreate(BaseSchema):
    address: Optional["Customer.CreateParamsAddress"] = Field(default=None)
    balance: Optional[int] = Field(default=None)
    cash_balance: Optional["Customer.CreateParamsCashBalance"] = Field(default=None)
    description: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    expand: Optional[list[str]] = Field(default=None)
    invoice_prefix: Optional[str] = Field(default=None)
    invoice_settings: Optional["Customer.CreateParamsInvoiceSettings"] = Field(default=None)
    metadata: Optional[dict[str, str]] = Field(default=None)
    name: Optional[str] = Field(default=None)
    next_invoice_sequence: Optional[int] = Field(default=None)
    payment_method: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    preferred_locales: Optional[list[str]] = Field(default=None)
    shipping: Optional["Customer.CreateParamsShipping"] = Field(default=None)
