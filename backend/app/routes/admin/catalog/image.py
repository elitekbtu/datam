import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.models.catalog import Product
from app.routes.admin.catalog.dependencies import TargetProduct
from app.schemas.catalog import ImageOrder, ProductImageCreate, ProductRead
from app.services.catalog import gallery
from app.services.catalog.storage import IMAGE_TYPES
from core.dependencies import DbSession, require_admin

router = APIRouter(
    prefix="/products/{product_id}/images",
    tags=["Admin · Photos"],
    dependencies=[Depends(require_admin)],
)

Upload = Annotated[
    UploadFile, File(description=f"One of: {', '.join(sorted(IMAGE_TYPES))}")
]
VariantField = Annotated[
    uuid.UUID | None,
    Form(description="Photo of this variant only; shared when omitted"),
]
AltTextField = Annotated[str | None, Form(max_length=255)]


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a photo that is already hosted somewhere",
)
async def add_image(
    product: TargetProduct, payload: ProductImageCreate, db: DbSession
) -> Product:
    return await gallery.add(db, product, payload)


@router.post(
    "/upload",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a photo from disk",
)
async def upload_image(
    product: TargetProduct,
    db: DbSession,
    file: Upload,
    variant_id: VariantField = None,
    alt_text: AltTextField = None,
    is_primary: Annotated[bool, Form()] = False,
) -> Product:
    return await gallery.upload(
        db,
        product,
        file,
        variant_id=variant_id,
        alt_text=alt_text,
        is_primary=is_primary,
    )


@router.delete("/{image_id}", response_model=ProductRead, summary="Remove a photo")
async def remove_image(
    product: TargetProduct, image_id: uuid.UUID, db: DbSession
) -> Product:
    return await gallery.remove(db, product, image_id)


@router.put("/order", response_model=ProductRead, summary="Reorder one gallery")
async def reorder_images(
    product: TargetProduct, payload: ImageOrder, db: DbSession
) -> Product:
    return await gallery.reorder(db, product, payload.image_ids)


@router.put(
    "/{image_id}/primary",
    response_model=ProductRead,
    summary="Make a photo the main one of its gallery",
)
async def set_primary_image(
    product: TargetProduct, image_id: uuid.UUID, db: DbSession
) -> Product:
    return await gallery.set_primary(db, product, image_id)
