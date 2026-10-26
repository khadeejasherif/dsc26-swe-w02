"""HTTP layer for the Tawseel parcel service.

The HTTP layer translates requests into calls to app.domain; the domain decides.
See README.md for the four operations, their operationIds and their errors.
"""


import base64
import binascii
from fastapi import FastAPI, Response
# ❌ Change this if you have it:
# from dataclasses import field  (or similar)
from uuid import uuid4
from fastapi import Query
from pydantic import BaseModel, Field
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.domain import EventType, InvalidTransition, Parcel, ParcelState, apply_event  # noqa: F401


class Problem(BaseModel):
    """A problem+json response body.

    See https://datatracker.ietf.org/doc/html/rfc7807
    """
    type: str
    title: str
    status: int
    detail: str | None = None
    errors: list[dict] | None = None


PROBLEM_DOC = {"model": Problem,
               "content": {"application/problem+json": {}}}


class ParcelIn(BaseModel):
    """The request body for the createParcel operation."""
    merchant_ref: str  = Field(min_length=1, max_length=64)
    cod_amount_piastres: int =Field(ge=0, le=5_000_000)
    address_text: str  = Field(min_length=1, max_length=500)


class ParcelEventRequest(BaseModel):
    type: EventType





class ParcelOut(BaseModel):
    id: str
    merchant_ref: str  = Field(min_length=1, max_length=64)
    cod_amount_piastres: int = Field(ge=0, le=5_000_000)
    address_text: str  = Field(min_length=1, max_length=500)
    state: ParcelState
    attempts: int

class ParcelListOut(BaseModel):
    items: list[ParcelOut]
    next_cursor: str | None = None

async def validation_problem(
    request: Request,
    exc: RequestValidationError,
):
    body = {
        "type": "/problems/validation",
        "title": "Request is not valid",
        "status": 422,
        "errors": [
            {
                "loc": list(e["loc"]),
                "msg": e["msg"],
            }
            for e in exc.errors()
        ],
    }

    return JSONResponse(
        status_code=422,
        media_type="application/problem+json",
        content=body,
    )

async def http_problem(request: Request, exc: HTTPException):
    titles = {
        404: "Not Found",
        409: "Conflict",
        400: "Bad Request",
        422: "Unprocessable Content",
    }

    body = {
        "type": f"/problems/{exc.status_code}",
        "title": titles.get(exc.status_code, "HTTP Error"),
        "status": exc.status_code,
        "detail": str(exc.detail),
       
    }

    return JSONResponse(
        status_code=exc.status_code,
        media_type="application/problem+json",
        content=body,
        headers=exc.headers,
    )





def create_app() -> FastAPI:
  
    app = FastAPI()
    parcels = {}

    app.add_exception_handler(
        RequestValidationError,
        validation_problem,
       
    )
    app.add_exception_handler(HTTPException, http_problem)



  


    @app.post("/v1/parcels",status_code=201, response_model=ParcelOut,operation_id="createParcel",responses={409: PROBLEM_DOC, 422: PROBLEM_DOC})
    def createParcel(parcel: ParcelIn ,  response: Response,) -> ParcelOut:
        if any(
        p.merchant_ref == parcel.merchant_ref
        for p in parcels.values()
        ):
         raise HTTPException(
            status_code=409,
            detail="Duplicate merchant_ref",
         )

        parcel_id = f"pcl_{uuid4().hex}"
        new_parcel = Parcel(
            id=parcel_id,
            merchant_ref=parcel.merchant_ref,
            cod_amount_piastres=parcel.cod_amount_piastres,
            address_text=parcel.address_text,
           

        )
        response.headers["Location"] = f"/v1/parcels/{parcel_id}"
        parcels[parcel_id] = new_parcel
        return new_parcel

    @app.get("/v1/parcels/{parcel_id}", response_model=ParcelOut,operation_id="getParcel",responses={404: PROBLEM_DOC})
    def getParcel(parcel_id: str) -> ParcelOut:
        parcel = parcels.get(parcel_id)
        if not parcel:
            raise HTTPException(
                status_code=404,
                detail=f"Parcel {parcel_id} not found",
            )
        return parcel

    @app.post("/v1/parcels/{parcel_id}/events", response_model=ParcelOut,operation_id="recordParcelEvent",responses={404: PROBLEM_DOC, 409: PROBLEM_DOC, 422: PROBLEM_DOC})
    def recordParcelEvent(parcel_id: str, event_request: ParcelEventRequest) -> Parcel:
        parcel = parcels.get(parcel_id)
        if not parcel:
            raise HTTPException(
                status_code=404,
                detail=f"Parcel {parcel_id} not found",
            )
        try:
            updated_parcel = apply_event(parcel, event_request.type)
        except InvalidTransition as e:
            raise HTTPException(
                status_code=409,
                detail=str(e),
            )
        parcels[parcel_id] = updated_parcel
        return updated_parcel

    @app.get("/v1/parcels", response_model=ParcelListOut, operation_id="listParcels", responses={400: PROBLEM_DOC, 422: PROBLEM_DOC})
    def listParcels(state: ParcelState | None = None, limit: int = Query(default=20, ge=1, le=100), cursor: str | None = None) -> ParcelListOut:
        all_parcels = list(parcels.values())

        if cursor is not None:
            try:
                decoded = base64.b64decode(cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True).decode("utf-8")
                canonical = base64.urlsafe_b64encode(decoded.encode("utf-8")).decode("ascii").rstrip("=")
                if canonical != cursor:
                    raise ValueError("Invalid cursor")
            except (ValueError, UnicodeDecodeError, binascii.Error):
                raise HTTPException(status_code=400, detail="Invalid cursor")

            cursor_index = next((i for i, p in enumerate(all_parcels) if p.id == decoded), None)
            if cursor_index is None:
                raise HTTPException(status_code=400, detail="Invalid cursor")
            remaining = all_parcels[cursor_index + 1:]
        else:
            remaining = all_parcels

        if state is not None:
            remaining = [p for p in remaining if p.state == state]

        page = remaining[:limit + 1]
        has_more = len(page) > limit
        items = page[:limit]
        next_cursor = None

        if has_more and items:
            next_cursor = base64.urlsafe_b64encode(items[-1].id.encode("utf-8")).decode("ascii").rstrip("=")

        return ParcelListOut(items=items, next_cursor=next_cursor)
    
    return app
    # raise NotImplementedError


# `uvicorn app.api:app` needs a module-level app. Once create_app() works,
# replace the line below with:  app = create_app()
app = create_app()
