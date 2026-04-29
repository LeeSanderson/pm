from fastapi import APIRouter, Depends, HTTPException, status

from app.board_store import BoardStore, BoardValidationError, CardNotFoundError, ColumnNotFoundError
from app.dependencies import get_board_store, require_authenticated_username
from app.models import CreateCardRequest, MoveCardRequest, RenameColumnRequest, UpdateCardRequest

router = APIRouter(prefix="/api/board", tags=["board"])


@router.get("")
def read_board(
  username: str = Depends(require_authenticated_username),
  board_store: BoardStore = Depends(get_board_store),
) -> dict[str, object]:
  return board_store.get_board(username)


@router.patch("/columns/{column_id}")
def rename_column(
  column_id: str,
  payload: RenameColumnRequest,
  username: str = Depends(require_authenticated_username),
  board_store: BoardStore = Depends(get_board_store),
) -> dict[str, object]:
  try:
    return board_store.rename_column(username, column_id, payload.title)
  except ColumnNotFoundError as error:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
  except BoardValidationError as error:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/columns/{column_id}/cards")
def create_card(
  column_id: str,
  payload: CreateCardRequest,
  username: str = Depends(require_authenticated_username),
  board_store: BoardStore = Depends(get_board_store),
) -> dict[str, object]:
  try:
    return board_store.add_card(username, column_id, payload.title, payload.details)
  except ColumnNotFoundError as error:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
  except BoardValidationError as error:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.patch("/cards/{card_id}")
def update_card(
  card_id: str,
  payload: UpdateCardRequest,
  username: str = Depends(require_authenticated_username),
  board_store: BoardStore = Depends(get_board_store),
) -> dict[str, object]:
  try:
    return board_store.update_card(username, card_id, payload.title, payload.details)
  except CardNotFoundError as error:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
  except BoardValidationError as error:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/columns/{column_id}/cards/{card_id}")
def delete_card(
  column_id: str,
  card_id: str,
  username: str = Depends(require_authenticated_username),
  board_store: BoardStore = Depends(get_board_store),
) -> dict[str, object]:
  try:
    return board_store.delete_card(username, column_id, card_id)
  except CardNotFoundError as error:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.patch("/cards/{card_id}/move")
def move_card(
  card_id: str,
  payload: MoveCardRequest,
  username: str = Depends(require_authenticated_username),
  board_store: BoardStore = Depends(get_board_store),
) -> dict[str, object]:
  try:
    return board_store.move_card(
      username,
      card_id,
      payload.column_id,
      payload.position,
    )
  except (ColumnNotFoundError, CardNotFoundError) as error:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
  except BoardValidationError as error:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
