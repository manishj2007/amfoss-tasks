import sys
import csv
import mysql.connector as mysql
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QGridLayout,
    QTextEdit, QSizePolicy, QLineEdit, QFileDialog
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

DB = dict(host="localhost", user="cine", password="cinepass", database="cinescope")

DEFAULT_COLS = ["Series_Title", "Released_Year", "Genre", "IMDB_Rating", "Director"]

SEARCH_COL = {
    "genre": "Genre",
    "year": "Released_Year",
    "rating": "IMDB_Rating",
    "director": "Director",
    "actor": "Star1",
}

COL_MAP = {
    "title": "Series_Title",
    "year": "Released_Year",
    "genre": "Genre",
    "rating": "IMDB_Rating",
    "director": "Director",
    "stars": "Star1",
}

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CineScope – Dashboard")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet("background-color: #121212; color: white; padding: 20px;")
        self.init_ui()
        self.search_mode = None
        self.selected_cols = set()
        self._last_headers = []
        self._conn = None

    def _conn_ok(self):
        if self._conn is None or not self._conn.is_connected():
            self._conn = mysql.connect(**DB)
        return self._conn

    def init_ui(self):
        main_layout = QVBoxLayout()
        header = QLabel("🎬 CineScope Dashboard")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setFixedHeight(80)
        main_layout.addWidget(header)

        split_layout = QHBoxLayout()
        left_container = QVBoxLayout()

        search_heading = QLabel("Search By")
        search_heading.setFont(QFont("Arial", 18, QFont.Bold))
        left_container.addWidget(search_heading)

        search_buttons = [
            ("Genre", "genre"),
            ("Year", "year"),
            ("Rating", "rating"),
            ("Director", "director"),
            ("Actor", "actor"),
        ]

        search_grid = QGridLayout()
        for index, (label, mode) in enumerate(search_buttons):
            btn = QPushButton(label)
            btn.setStyleSheet(self.get_button_style(False))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(lambda _, m=mode: self.set_search_mode(m))
            row, col = divmod(index, 2)
            search_grid.addWidget(btn, row, col)
        left_container.addLayout(search_grid)

        column_heading = QLabel("Select Columns")
        column_heading.setFont(QFont("Arial", 18, QFont.Bold))
        left_container.addWidget(column_heading)

        column_buttons = [
            ("Title", "title"),
            ("Year", "year"),
            ("Genre", "genre"),
            ("Rating", "rating"),
            ("Director", "director"),
            ("Stars", "stars"),
        ]

        column_grid = QGridLayout()
        for index, (label, col_key) in enumerate(column_buttons):
            btn = QPushButton(label)
            btn.setStyleSheet(self.get_button_style(False))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(lambda _, c=col_key: self.toggle_column(c))
            row, col = divmod(index, 2)
            column_grid.addWidget(btn, row, col)
        left_container.addLayout(column_grid)

        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter search term")
        self.query_input.setStyleSheet("background-color: #1e1e1e; color: white; padding: 5px; border: 1px solid #444;")
        left_container.addWidget(self.query_input)

        action_layout = QHBoxLayout()
        search_btn = QPushButton("Search")
        search_btn.setStyleSheet("background-color: #e50914; color: white; padding: 6px; border-radius: 5px;")
        search_btn.clicked.connect(self.execute_search)
        action_layout.addWidget(search_btn)

        export_btn = QPushButton("Export CSV")
        export_btn.setStyleSheet("background-color: #1f1f1f; color: white; padding: 6px; border-radius: 5px;")
        export_btn.clicked.connect(self.export_csv)
        action_layout.addWidget(export_btn)
        left_container.addLayout(action_layout)

        right_side_layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                color: white;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: white;
                color: black;
                padding: 4px;
            }
        """)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.output_console = QTextEdit()
        self.output_console.setPlaceholderText("Results will appear here...")
        self.output_console.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #444;
                padding: 5px;
            }
        """)
        self.output_console.setFixedHeight(100)

        right_side_layout.addWidget(self.table)
        right_side_layout.addWidget(self.output_console)

        split_layout.addLayout(left_container, 2)
        split_layout.addLayout(right_side_layout, 8)
        main_layout.addLayout(split_layout)
        self.setLayout(main_layout)

    def get_button_style(self, is_selected):
        if is_selected:
            return """
                QPushButton {
                    background-color: #ffcc00;
                    border: 1px solid #ff9900;
                    border-radius: 3px;
                    padding: 6px;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #1f1f1f;
                    border: 1px solid #333;
                    border-radius: 3px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background-color: #333;
                }
            """

    def set_search_mode(self, mode):
        self.search_mode = mode
        self.output_console.append(f"Search mode set to: {mode}")

    def toggle_column(self, column):
        if column in self.selected_cols:
            self.selected_cols.remove(column)
            self.output_console.append(f"Column OFF: {column}")
        else:
            self.selected_cols.add(column)
            self.output_console.append(f"Column ON: {column}")

    def execute_search(self):
        text = self.query_input.text().strip()
        cols = [COL_MAP[c] for c in self.selected_cols] if self.selected_cols else DEFAULT_COLS
        col_sql = ", ".join(cols)
        sql = f"SELECT {col_sql} FROM movies"
        params = []
        if text:
            if self.search_mode and self.search_mode in SEARCH_COL:
                col = SEARCH_COL[self.search_mode]
            else:
                col = "Series_Title"
            if col in ("Released_Year", "IMDB_Rating") and text.endswith("+") and text[:-1].isdigit():
                sql += f" WHERE {col} >= %s"
                params.append(int(text[:-1]))
            elif col in ("Released_Year", "IMDB_Rating") and text.isdigit():
                sql += f" WHERE {col} = %s"
                params.append(int(text))
            else:
                sql += f" WHERE {col} LIKE %s"
                params.append(f"%{text}%")
        if "IMDB_Rating" in cols:
            sql += " ORDER BY IMDB_Rating DESC"
        elif "Released_Year" in cols:
            sql += " ORDER BY Released_Year DESC"
        sql += " LIMIT 500"
        try:
            conn = self._conn_ok()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            cur.close()
            self.table.clear()
            self.table.setRowCount(len(rows))
            self.table.setColumnCount(len(cols))
            self.table.setHorizontalHeaderLabels(cols)
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))
            self.table.resizeColumnsToContents()
            self._last_headers = cols[:]
            self.output_console.append(f"Found {len(rows)} rows")
        except Exception as e:
            self.output_console.append(f"ERROR: {e}")

    def export_csv(self):
        if self.table.rowCount() == 0:
            self.output_console.append("Nothing to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "cinescope_export.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                headers = self._last_headers if self._last_headers else [
                    self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())
                ]
                w.writerow(headers)
                for r in range(self.table.rowCount()):
                    row = []
                    for c in range(self.table.columnCount()):
                        it = self.table.item(r, c)
                        row.append("" if it is None else it.text())
                    w.writerow(row)
            self.output_console.append(f"Exported {self.table.rowCount()} rows → {path}")
        except Exception as e:
            self.output_console.append(f"Export failed: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec())
