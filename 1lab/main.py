import pygame as pg
import sys
from copy import deepcopy
from enum import Enum


class PieceType(Enum):
    PAWN = "Pawn"
    ROOK = "Rook"
    KNIGHT = "Knight"
    BISHOP = "Bishop"
    QUEEN = "Queen"
    KING = "King"


class Color(Enum):
    WHITE = "White"
    BLACK = "Black"


class Move:
    def __init__(self, piece, from_x, from_y, to_x, to_y, move_type, captured=None, rook_info=None):
        self.piece = piece
        self.from_x = from_x
        self.from_y = from_y
        self.to_x = to_x
        self.to_y = to_y
        self.move_type = move_type
        self.captured = captured
        self.rook_info = rook_info
        self.piece_state = {
            'is_moved': piece.is_moved,
            'step': piece.step if hasattr(piece, 'step') else None
        }


class GameState:
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.pieces = []
        self.white_king = None
        self.black_king = None
        self.current_turn = Color.WHITE
        self.move_stack = []
        self.move_history = []
        self.last_move = None
        self.move_number = 1
        self.game_over = False
        self.winner = None
        
    def switch_turn(self):
        self.current_turn = Color.BLACK if self.current_turn == Color.WHITE else Color.WHITE
        if self.current_turn == Color.WHITE:
            self.move_number += 1
            
    def get_piece_at(self, x, y):
        if 0 <= x < 8 and 0 <= y < 8:
            return self.board[y][x]
        return None
        
    def get_king(self, color):
        return self.white_king if color == Color.WHITE else self.black_king


class Piece:
    def __init__(self, game_state, piece_type, x, y, color):
        self.game = game_state
        self.piece_type = piece_type
        self.x = x
        self.y = y
        self.color = color
        self.is_moved = False
        self.status = "Alive"
        
    def get_symbol(self):
        symbols = {
            (PieceType.KING, Color.WHITE): "♔",
            (PieceType.QUEEN, Color.WHITE): "♕",
            (PieceType.ROOK, Color.WHITE): "♖",
            (PieceType.BISHOP, Color.WHITE): "♗",
            (PieceType.KNIGHT, Color.WHITE): "♘",
            (PieceType.PAWN, Color.WHITE): "♙",
            (PieceType.KING, Color.BLACK): "♚",
            (PieceType.QUEEN, Color.BLACK): "♛",
            (PieceType.ROOK, Color.BLACK): "♜",
            (PieceType.BISHOP, Color.BLACK): "♝",
            (PieceType.KNIGHT, Color.BLACK): "♞",
            (PieceType.PAWN, Color.BLACK): "♟",
        }
        return symbols.get((self.piece_type, self.color), "?")
        
    def can_move_to(self, x, y):
        return False
        
    def move(self, to_x, to_y):
        if not self.can_move_to(to_x, to_y):
            return False
            
        captured = self.game.get_piece_at(to_x, to_y)
        move = Move(self, self.x, self.y, to_x, to_y, 'normal', captured)
        
        self.game.board[self.y][self.x] = None
        if captured:
            captured.status = "Killed"
            self.game.pieces.remove(captured)
            
        self.x = to_x
        self.y = to_y
        self.game.board[self.y][self.x] = self
        self.is_moved = True
        
        self.game.move_stack.append(move)
        self.game.move_history.append(self._format_move(move))
        self.game.last_move = (move.from_x, move.from_y, to_x, to_y)
        
        if self.piece_type == PieceType.PAWN and (self.y == 0 or self.y == 7):
            self._promote()
            
        self.game.switch_turn()
        self._check_game_over()
        
        return True
        
    def _format_move(self, move):
        from_pos = chr(move.from_x + 97) + str(8 - move.from_y)
        to_pos = chr(move.to_x + 97) + str(8 - move.to_y)
        piece_symbol = self.get_symbol()
        return f"{piece_symbol}{from_pos}-{to_pos}"
        
    def _promote(self):
        print("\nДоступные фигуры: Queen Knight Bishop Rook")
        promotion_map = {
            "QUEEN": PieceType.QUEEN,
            "KNIGHT": PieceType.KNIGHT,
            "BISHOP": PieceType.BISHOP,
            "ROOK": PieceType.ROOK
        }
        
        while True:
            choice = input("Выберите фигуру для превращения >> ").strip().upper()
            if choice in promotion_map:
                new_piece = create_piece(self.game, promotion_map[choice], self.x, self.y, self.color)
                self.game.board[self.y][self.x] = new_piece
                self.game.pieces.remove(self)
                self.game.pieces.append(new_piece)
                break
            print("Неверный выбор! Попробуйте снова.")
            
    def _check_game_over(self):
        king = self.game.get_king(self.game.current_turn)
        if king and self._is_checkmate(king):
            self.game.game_over = True
            self.game.winner = Color.WHITE if self.game.current_turn == Color.BLACK else Color.BLACK
            
    def _is_checkmate(self, king):
        if not self._is_square_attacked(king.x, king.y, king.color):
            return False
            
        for piece in self.game.pieces:
            if piece.color == king.color and piece.status == "Alive":
                for y in range(8):
                    for x in range(8):
                        if piece.can_move_to(x, y):
                            if self._move_removes_check(piece, x, y, king):
                                return False
        return True
        
    def _move_removes_check(self, piece, to_x, to_y, king):
        old_x, old_y = piece.x, piece.y
        captured = self.game.get_piece_at(to_x, to_y)
        
        self.game.board[old_y][old_x] = None
        if captured:
            self.game.pieces.remove(captured)
        piece.x, piece.y = to_x, to_y
        self.game.board[to_y][to_x] = piece
        
        in_check = self._is_square_attacked(king.x, king.y, king.color)
        
        piece.x, piece.y = old_x, old_y
        self.game.board[old_y][old_x] = piece
        self.game.board[to_y][to_x] = captured
        if captured:
            self.game.pieces.append(captured)
            
        return not in_check
        
    def _is_square_attacked(self, x, y, color):
        for piece in self.game.pieces:
            if piece.color != color and piece.status == "Alive":
                if piece._can_attack(x, y):
                    return True
        return False
        
    def _can_attack(self, x, y):
        return self.can_move_to(x, y)
        
    def _is_path_clear(self, to_x, to_y):
        dx = 0 if to_x == self.x else (1 if to_x > self.x else -1)
        dy = 0 if to_y == self.y else (1 if to_y > self.y else -1)
        
        x, y = self.x + dx, self.y + dy
        while (x, y) != (to_x, to_y):
            if self.game.get_piece_at(x, y) is not None:
                return False
            x += dx
            y += dy
        return True


class Pawn(Piece):
    def __init__(self, game_state, x, y, color):
        super().__init__(game_state, PieceType.PAWN, x, y, color)
        self.step = 0
        
    def can_move_to(self, to_x, to_y):
        direction = 1 if self.color == Color.WHITE else -1
        dx = to_x - self.x
        dy = to_y - self.y
        
        if dx == 0 and dy == -direction:
            return self.game.get_piece_at(to_x, to_y) is None
            
        if dx == 0 and dy == -2 * direction and not self.is_moved:
            mid_y = self.y - direction
            return (self.game.get_piece_at(to_x, to_y) is None and 
                   self.game.get_piece_at(to_x, mid_y) is None)
                   
        if abs(dx) == 1 and dy == -direction:
            target = self.game.get_piece_at(to_x, to_y)
            if target and target.color != self.color:
                return True
                
            last_move = self.game.last_move
            if last_move:
                last_from_x, last_from_y, last_to_x, last_to_y = last_move
                last_piece = self.game.get_piece_at(last_to_x, last_to_y)
                if (last_piece and last_piece.piece_type == PieceType.PAWN and 
                    last_piece.color != self.color and abs(last_to_y - last_from_y) == 2 and
                    last_to_x == to_x and last_to_y == self.y):
                    return True
                    
        return False


class Rook(Piece):
    def __init__(self, game_state, x, y, color):
        super().__init__(game_state, PieceType.ROOK, x, y, color)
        
    def can_move_to(self, to_x, to_y):
        if (self.x == to_x) != (self.y == to_y):
            if self._is_path_clear(to_x, to_y):
                target = self.game.get_piece_at(to_x, to_y)
                return target is None or target.color != self.color
        return False


class Knight(Piece):
    def __init__(self, game_state, x, y, color):
        super().__init__(game_state, PieceType.KNIGHT, x, y, color)
        
    def can_move_to(self, to_x, to_y):
        dx = abs(to_x - self.x)
        dy = abs(to_y - self.y)
        if (dx == 2 and dy == 1) or (dx == 1 and dy == 2):
            target = self.game.get_piece_at(to_x, to_y)
            return target is None or target.color != self.color
        return False


class Bishop(Piece):
    def __init__(self, game_state, x, y, color):
        super().__init__(game_state, PieceType.BISHOP, x, y, color)
        
    def can_move_to(self, to_x, to_y):
        if abs(to_x - self.x) == abs(to_y - self.y):
            if self._is_path_clear(to_x, to_y):
                target = self.game.get_piece_at(to_x, to_y)
                return target is None or target.color != self.color
        return False


class Queen(Piece):
    def __init__(self, game_state, x, y, color):
        super().__init__(game_state, PieceType.QUEEN, x, y, color)
        
    def can_move_to(self, to_x, to_y):
        if (self.x == to_x) != (self.y == to_y) or abs(to_x - self.x) == abs(to_y - self.y):
            if self._is_path_clear(to_x, to_y):
                target = self.game.get_piece_at(to_x, to_y)
                return target is None or target.color != self.color
        return False


class King(Piece):
    def __init__(self, game_state, x, y, color):
        super().__init__(game_state, PieceType.KING, x, y, color)
        if color == Color.WHITE:
            game_state.white_king = self
        else:
            game_state.black_king = self
            
    def can_move_to(self, to_x, to_y):
        dx = abs(to_x - self.x)
        dy = abs(to_y - self.y)
        
        if max(dx, dy) == 1:
            target = self.game.get_piece_at(to_x, to_y)
            if (target is None or target.color != self.color) and not self._is_square_attacked(to_x, to_y, self.color):
                return True
                
        if not self.is_moved and dy == 0 and dx == 2:
            rook_x = 0 if to_x == 2 else 7
            rook = self.game.get_piece_at(rook_x, self.y)
            if (rook and rook.piece_type == PieceType.ROOK and not rook.is_moved and
                not self._is_square_attacked(self.x, self.y, self.color)):
                step = -1 if to_x == 2 else 1
                for x in range(self.x + step, to_x + step, step):
                    if self.game.get_piece_at(x, self.y) is not None:
                        return False
                    if self._is_square_attacked(x, self.y, self.color):
                        return False
                return True
                
        return False
        
    def _is_square_attacked(self, x, y, color):
        for piece in self.game.pieces:
            if piece.color != color and piece.status == "Alive":
                if piece._can_attack(x, y):
                    return True
        return False


def create_piece(game_state, piece_type, x, y, color):
    pieces = {
        PieceType.PAWN: Pawn,
        PieceType.ROOK: Rook,
        PieceType.KNIGHT: Knight,
        PieceType.BISHOP: Bishop,
        PieceType.QUEEN: Queen,
        PieceType.KING: King,
    }
    piece_class = pieces.get(piece_type)
    if piece_class:
        piece = piece_class(game_state, x, y, color)
        game_state.pieces.append(piece)
        game_state.board[y][x] = piece
        return piece
    return None


class ChessGame:
    def __init__(self):
        pg.init()
        self.game_state = GameState()
        self.screen = pg.display.set_mode((800, 700))
        pg.display.set_caption("Шахматы")
        self.clock = pg.time.Clock()
        self.selected_piece = None
        self.valid_moves = []
        self.running = True
        
        self._init_resources()
        self._init_board()
        
    def _init_resources(self):
        try:
            self.font = pg.font.SysFont("segoeuisymbol", 72)
            if self.font is None:
                self.font = pg.font.Font(None, 72)
            self.small_font = pg.font.Font(None, 36)
        except:
            self.font = pg.font.Font(None, 72)
            self.small_font = pg.font.Font(None, 36)
            
        self.board_img = self._create_board_image()
        
    def _create_board_image(self):
        board = pg.Surface((630, 630))
        colors = [(240, 217, 181), (181, 136, 99)]
        for y in range(8):
            for x in range(8):
                color = colors[(x + y) % 2]
                pg.draw.rect(board, color, (x * 70, y * 70, 70, 70))
        return board
        
    def _init_board(self):
        pieces_row = [
            PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP,
            PieceType.QUEEN, PieceType.KING, PieceType.BISHOP,
            PieceType.KNIGHT, PieceType.ROOK
        ]
        
        for x, piece_type in enumerate(pieces_row):
            create_piece(self.game_state, piece_type, x, 0, Color.BLACK)
            
        for x in range(8):
            create_piece(self.game_state, PieceType.PAWN, x, 1, Color.BLACK)
            
        for x in range(8):
            create_piece(self.game_state, PieceType.PAWN, x, 6, Color.WHITE)
            
        for x, piece_type in enumerate(pieces_row):
            create_piece(self.game_state, piece_type, x, 7, Color.WHITE)
        
    def run(self):
        self._show_instructions()
        
        while self.running:
            self._handle_events()
            self._draw()
            self.clock.tick(60)
            
        pg.quit()
        sys.exit()
        
    def _handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self._save_notation()
                self.running = False
                
            elif event.type == pg.MOUSEBUTTONDOWN:
                if not self.game_state.game_over:
                    self._handle_click()
                    
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_z and (pg.key.get_mods() & pg.KMOD_CTRL):
                    self._undo_move()
                elif event.key == pg.K_h and (pg.key.get_mods() & pg.KMOD_CTRL):
                    self._show_history()
                    
    def _handle_click(self):
        x, y = pg.mouse.get_pos()
        board_x = (x - 85) // 70
        board_y = (y - 35) // 70
        
        if not (0 <= board_x < 8 and 0 <= board_y < 8):
            return
            
        if self.selected_piece is None:
            piece = self.game_state.get_piece_at(board_x, board_y)
            if piece and piece.color == self.game_state.current_turn and piece.status == "Alive":
                self.selected_piece = piece
                self._calculate_valid_moves(piece)
        else:
            if (board_x, board_y) in self.valid_moves:
                if self.selected_piece.move(board_x, board_y):
                    self.selected_piece = None
                    self.valid_moves = []
            else:
                self.selected_piece = None
                self.valid_moves = []
                
    def _calculate_valid_moves(self, piece):
        self.valid_moves = []
        for y in range(8):
            for x in range(8):
                if piece.can_move_to(x, y):
                    self.valid_moves.append((x, y))
                    
    def _undo_move(self):
        if not self.game_state.move_stack:
            print("Нет ходов для отката!")
            return
            
        move = self.game_state.move_stack.pop()
        
        move.piece.x, move.piece.y = move.from_x, move.from_y
        move.piece.is_moved = move.piece_state['is_moved']
        if move.piece_state['step'] is not None:
            move.piece.step = move.piece_state['step']
            
        self.game_state.board[move.from_y][move.from_x] = move.piece
        self.game_state.board[move.to_y][move.to_x] = None
        
        if move.captured:
            move.captured.status = "Alive"
            move.captured.x, move.captured.y = move.to_x, move.to_y
            self.game_state.board[move.to_y][move.to_x] = move.captured
            self.game_state.pieces.append(move.captured)
            
        if move.rook_info:
            rook, rx, ry, _, _ = move.rook_info
            rook.x, rook.y = rx, ry
            rook.is_moved = False
            self.game_state.board[ry][rx] = rook
            
        self.game_state.switch_turn()
        
        if self.game_state.move_history:
            self.game_state.move_history.pop()
            
        self.game_state.last_move = None
        print("Откат хода выполнен")
        
    def _show_history(self):
        print("\n" + "=" * 60)
        print("ИСТОРИЯ ХОДОВ")
        print("=" * 60)
        if not self.game_state.move_history:
            print("История пуста")
        else:
            for i, move in enumerate(self.game_state.move_history, 1):
                num = (i + 1) // 2
                if i % 2 == 1:
                    print(f"{num:2}. {move:15}", end=" ")
                else:
                    print(f"{move}")
            if len(self.game_state.move_history) % 2 == 1:
                print()
        print("=" * 60)
        
    def _save_notation(self):
        try:
            with open('chess_notation.txt', 'w', encoding='utf-8') as f:
                for i, move in enumerate(self.game_state.move_history, 1):
                    num = (i + 1) // 2
                    if i % 2 == 1:
                        f.write(f"{num:2}. {move:15}")
                    else:
                        f.write(f"{move}\n")
                if len(self.game_state.move_history) % 2 == 1:
                    f.write("\n")
            print("Нотация сохранена в файл chess_notation.txt")
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            
    def _draw(self):
        self.screen.fill((50, 50, 50))
        self.screen.blit(self.board_img, (85, 35))
        
        for piece in self.game_state.pieces:
            if piece.status == "Alive":
                self._draw_piece(piece)
                
        if self.selected_piece:
            self._highlight_square(self.selected_piece.x, self.selected_piece.y, (0, 255, 0))
            
        for x, y in self.valid_moves:
            target = self.game_state.get_piece_at(x, y)
            color = (255, 0, 0) if target and target.color != self.selected_piece.color else (0, 0, 255)
            self._highlight_square(x, y, color, alpha=128)
            
        if self.game_state.last_move:
            from_x, from_y, to_x, to_y = self.game_state.last_move
            self._highlight_square(from_x, from_y, (0, 255, 0), alpha=100)
            self._highlight_square(to_x, to_y, (0, 255, 0), alpha=100)
            
        king = self.game_state.get_king(self.game_state.current_turn)
        if king and king._is_square_attacked(king.x, king.y, king.color):
            self._highlight_square(king.x, king.y, (255, 0, 0), alpha=150)
            
        self._draw_info()
        
        if self.game_state.game_over:
            self._draw_game_over()
            
        pg.display.flip()
        
    def _draw_piece(self, piece):
        symbol = piece.get_symbol()
        text = self.font.render(symbol, True, (0, 0, 0))
        text_rect = text.get_rect(center=(85 + piece.x * 70 + 35, 35 + piece.y * 70 + 35))
        self.screen.blit(text, text_rect)
        
    def _highlight_square(self, x, y, color, alpha=100):
        highlight = pg.Surface((70, 70))
        highlight.set_alpha(alpha)
        highlight.fill(color)
        self.screen.blit(highlight, (85 + x * 70, 35 + y * 70))
        
    def _draw_info(self):
        turn_text = f"Ход: {self.game_state.current_turn.value}"
        text = self.small_font.render(turn_text, True, (255, 255, 255))
        self.screen.blit(text, (10, 10))
        
        move_text = f"Ход номер: {self.game_state.move_number}"
        text = self.small_font.render(move_text, True, (255, 255, 255))
        self.screen.blit(text, (10, 50))
        
    def _draw_game_over(self):
        overlay = pg.Surface((800, 700))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        winner_text = f"ПОБЕДА {self.game_state.winner.value.upper()}!"
        text = self.font.render(winner_text, True, (255, 255, 0))
        text_rect = text.get_rect(center=(400, 350))
        self.screen.blit(text, text_rect)
        
    def _show_instructions(self):
        print("\n" + "=" * 60)
        print("ШАХМАТЫ")
        print("=" * 60)
        print("Управление:")
        print("  ЛКМ по фигуре -> выбор, ЛКМ по клетке -> ход")
        print("  Ctrl+Z -> откат последнего хода")
        print("  Ctrl+H -> показать историю ходов")
        print("=" * 60 + "\n")


def main():
    ChessGame().run()


if __name__ == "__main__":
    main()
