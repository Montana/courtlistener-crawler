#!/usr/bin/env python3

import sys
import os
import csv
import requests
from datetime import datetime
from typing import Dict, List, Optional, Union
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget,
                            QTableWidgetItem, QDateEdit, QSpinBox, QCheckBox, QFileDialog,
                            QTabWidget, QMessageBox, QGroupBox, QStatusBar, QHeaderView,
                            QSplitter, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPixmap

API_BASE = "https://www.courtlistener.com/api/rest/v4"
API_TOKEN = ""

HEADERS = {
    "User-Agent": "CourtListenerGUI/1.0",
    "Authorization": f"Token {API_TOKEN}",
}

POPULAR_COURTS = [
    ("", "All Courts"),
    ("scotus", "Supreme Court of the United States"),
    ("ca9", "U.S. Court of Appeals for the Ninth Circuit"),
    ("ca2", "U.S. Court of Appeals for the Second Circuit"),
    ("ca5", "U.S. Court of Appeals for the Fifth Circuit"),
    ("ca1", "U.S. Court of Appeals for the First Circuit"),
    ("dc", "U.S. District Court for the District of Columbia"),
    ("nysd", "U.S. District Court for the Southern District of New York"),
    ("nyed", "U.S. District Court for the Eastern District of New York"),
    ("cand", "U.S. District Court for the Northern District of California"),
    ("cacd", "U.S. District Court for the Central District of California"),
]

court_cache: Dict[str, str] = {}

class StyledButton(QPushButton):
    def __init__(self, text, color="#1E88E5", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}DD;
            }}
            QPushButton:pressed {{
                background-color: {color}AA;
            }}
            QPushButton:disabled {{
                background-color: #424242;
                color: #757575;
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)

class CourtListenerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.search_results = []
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
                color: #E0E0E0;
            }
            QTabWidget::pane {
                border: 1px solid #424242;
                background-color: #212121;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #323232;
                color: #E0E0E0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #212121;
                border: 1px solid #424242;
                border-bottom-color: #212121;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #424242;
                border-radius: 4px;
                margin-top: 1.5ex;
                color: #E0E0E0;
                background-color: #212121;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: #212121;
            }
            QLineEdit, QComboBox, QDateEdit, QSpinBox {
                padding: 6px;
                border: 1px solid #424242;
                border-radius: 4px;
                background-color: #323232;
                color: #E0E0E0;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox::down-arrow {
                background-color: #323232;
            }
            QComboBox QAbstractItemView {
                background-color: #323232;
                color: #E0E0E0;
                selection-background-color: #424242;
            }
            QCheckBox {
                color: #E0E0E0;
            }
            QCheckBox::indicator {
                border: 1px solid #424242;
                background: #323232;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {
                border: 1px solid #2196F3;
            }
            QTableWidget {
                border: none;
                gridline-color: #424242;
                border-radius: 4px;
                background-color: #212121;
                color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #323232;
                padding: 6px;
                border: none;
                border-right: 1px solid #424242;
                font-weight: bold;
                color: #E0E0E0;
            }
            QStatusBar {
                background-color: #323232;
                color: #E0E0E0;
            }
            QLabel {
                color: #E0E0E0;
            }
            QToolTip {
                background-color: #323232;
                color: #E0E0E0;
                border: 1px solid #424242;
            }
        """)
        
    def init_ui(self):
        self.setWindowTitle("CourtListener Search Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        tab_widget = QTabWidget()
        tab_widget.setDocumentMode(True)
        main_layout.addWidget(tab_widget)
        
        search_tab = QWidget()
        search_layout = QVBoxLayout(search_tab)
        search_layout.setContentsMargins(15, 15, 15, 15)
        search_layout.setSpacing(15)
        
        header_label = QLabel("CourtListener Search")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("color: #64B5F6;")
        search_layout.addWidget(header_label)
        
        query_group = QGroupBox("Search Parameters")
        query_layout = QVBoxLayout(query_group)
        query_layout.setContentsMargins(15, 20, 15, 15)
        query_layout.setSpacing(15)
        
        query_input_layout = QHBoxLayout()
        query_label = QLabel("Search Query:")
        query_label.setMinimumWidth(100)
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter search terms (e.g., 'First Amendment', 'Chevron deference')")
        query_input_layout.addWidget(query_label)
        query_input_layout.addWidget(self.query_input)
        query_layout.addLayout(query_input_layout)
        
        court_layout = QHBoxLayout()
        court_label = QLabel("Court:")
        court_label.setMinimumWidth(100)
        self.court_combo = QComboBox()
        for slug, name in POPULAR_COURTS:
            self.court_combo.addItem(name, slug)
        court_layout.addWidget(court_label)
        court_layout.addWidget(self.court_combo)
        query_layout.addLayout(court_layout)
        
        date_layout = QHBoxLayout()
        date_group = QGroupBox("Date Range")
        date_group_layout = QHBoxLayout(date_group)
        date_group_layout.setContentsMargins(15, 15, 15, 15)
        date_group_layout.setSpacing(10)
        
        start_date_label = QLabel("Start:")
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-3))
        
        end_date_label = QLabel("End:")
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        
        date_group_layout.addWidget(start_date_label)
        date_group_layout.addWidget(self.start_date)
        date_group_layout.addWidget(end_date_label)
        date_group_layout.addWidget(self.end_date)
        
        self.use_date_range = QCheckBox("Enable Date Range")
        date_group_layout.addWidget(self.use_date_range)
        
        limit_label = QLabel("Max Results:")
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 500)
        self.limit_spin.setValue(50)
        date_group_layout.addWidget(limit_label)
        date_group_layout.addWidget(self.limit_spin)
        
        date_layout.addWidget(date_group)
        query_layout.addLayout(date_layout)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.search_button = StyledButton("Search Opinions", "#2196F3")
        self.search_button.clicked.connect(self.search_opinions)
        
        self.current_button = StyledButton("Recent Opinions", "#4CAF50")
        self.current_button.clicked.connect(self.fetch_current_opinions)
        
        self.export_button = StyledButton("Export to CSV", "#FF9800")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        
        buttons_layout.addWidget(self.search_button)
        buttons_layout.addWidget(self.current_button)
        buttons_layout.addWidget(self.export_button)
        query_layout.addLayout(buttons_layout)
        
        search_layout.addWidget(query_group)
        
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        results_layout.setContentsMargins(10, 20, 10, 10)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels(["Case Name", "Court", "Date Filed", "URL", "Docket Number", "Citation"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setAlternatingRowColors(False)
        self.results_table.setStyleSheet("""
            QTableWidget {
                background-color: #212121;
                color: #E0E0E0;
            }
            QTableWidget::item {
                background-color: #212121;
            }
            QTableWidget::item:selected {
                background-color: #1565C0;
                color: white;
            }
        """)
        
        results_layout.addWidget(self.results_table)
        search_layout.addWidget(results_group)
        
        tab_widget.addTab(search_tab, "Search")
        
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(15, 15, 15, 15)
        settings_layout.setSpacing(15)
        
        settings_header = QLabel("Settings")
        settings_header.setFont(header_font)
        settings_header.setAlignment(Qt.AlignCenter)
        settings_header.setStyleSheet("color: #64B5F6;")
        settings_layout.addWidget(settings_header)
        
        api_group = QGroupBox("API Configuration")
        api_layout = QVBoxLayout(api_group)
        api_layout.setContentsMargins(15, 20, 15, 15)
        api_layout.setSpacing(15)
        
        token_info = QLabel("Enter your CourtListener API token below. You can obtain a token from https://www.courtlistener.com/api/rest-info/")
        token_info.setWordWrap(True)
        api_layout.addWidget(token_info)
        
        token_layout = QHBoxLayout()
        token_label = QLabel("API Token:")
        token_label.setMinimumWidth(100)
        self.token_input = QLineEdit()
        self.token_input.setText(API_TOKEN)
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText("Enter your API token")
        token_layout.addWidget(token_label)
        token_layout.addWidget(self.token_input)
        
        save_token_button = StyledButton("Save Token", "#673AB7")
        save_token_button.clicked.connect(self.save_api_token)
        token_layout.addWidget(save_token_button)
        
        api_layout.addLayout(token_layout)
        settings_layout.addWidget(api_group)
        settings_layout.addStretch()
        
        tab_widget.addTab(settings_tab, "Settings")
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        self.progress_label = QLabel("")
        self.status_bar.addPermanentWidget(self.progress_label)
        
    def save_api_token(self):
        global API_TOKEN, HEADERS
        API_TOKEN = self.token_input.text()
        HEADERS["Authorization"] = f"Token {API_TOKEN}"
        QMessageBox.information(self, "Settings", "API Token saved successfully")
        
    def validate_date(self, date_str: str) -> bool:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
            
    def resolve_court_name(self, court_ref: Union[str, dict]) -> str:
        if isinstance(court_ref, dict):
            return court_ref.get("name", "Unknown Court")

        if isinstance(court_ref, str) and court_ref.startswith("/api/"):
            if court_ref in court_cache:
                return court_cache[court_ref]

            court_url = f"https://www.courtlistener.com{court_ref}"
            try:
                response = requests.get(court_url, headers=HEADERS, timeout=10)
                response.raise_for_status()
                name = response.json().get("name", court_ref.split("/")[-2])
                court_cache[court_ref] = name
                return name
            except requests.RequestException:
                return court_ref.split("/")[-2]

        return court_ref or "Unknown Court"

    def fetch_opinions(self, url: str, params: Dict[str, Union[str, int]]) -> List[Dict]:
        self.status_bar.showMessage("Fetching opinions...")
        all_results = []
        max_results = params.get("page_size", 20)
        
        original_page_size = params.get("page_size", 20)
        
        per_page = 20
        params["page_size"] = per_page
        
        pages_needed = (max_results + per_page - 1) // per_page
        
        try:
            next_url = url
            page = 1
            
            while next_url and len(all_results) < max_results and page <= pages_needed:
                self.status_bar.showMessage(f"Fetching page {page}...")
                self.progress_label.setText(f"Page {page}/{pages_needed}")
                
                if page > 1:
                    response = requests.get(next_url, headers=HEADERS, timeout=15)
                else:
                    response = requests.get(url, headers=HEADERS, params=params, timeout=15)
                
                response.raise_for_status()
                json_response = response.json()
                
                page_results = json_response.get("results", [])
                all_results.extend(page_results)
                
                next_url = json_response.get("next")
                page += 1
                
                if next_url and len(all_results) < max_results:
                    self.status_bar.showMessage(f"Fetched {len(all_results)} results so far...")
                    QApplication.processEvents()
            
            all_results = all_results[:original_page_size]
            
            self.status_bar.showMessage(f"Fetched {len(all_results)} opinions successfully")
            self.progress_label.setText("")
            return all_results
            
        except requests.ConnectionError:
            self.status_bar.showMessage("Connection error: Unable to reach the API.")
            self.progress_label.setText("")
            return all_results
        except requests.Timeout:
            self.status_bar.showMessage("Request timed out: API took too long to respond.")
            self.progress_label.setText("")
            return all_results
        except requests.HTTPError as e:
            self.status_bar.showMessage(f"HTTP error: {e.response.status_code} - {e.response.reason}")
            self.progress_label.setText("")
            return all_results
        except requests.RequestException as e:
            self.status_bar.showMessage(f"API error: {e}")
            self.progress_label.setText("")
            return all_results

    def display_results(self, results: List[Dict]):
        self.search_results = results
        self.results_table.setRowCount(0)
        
        if not results:
            self.status_bar.showMessage("No results found")
            self.export_button.setEnabled(False)
            return
            
        self.status_bar.showMessage(f"Found {len(results)} result(s)")
        self.export_button.setEnabled(True)
        
        for row, item in enumerate(results):
            self.results_table.insertRow(row)
            
            case_name = item.get("case_name", "Unknown Case")
            court = self.resolve_court_name(item.get("court"))
            date_filed = item.get("date_filed", "Unknown Date")
            absolute_url = item.get("absolute_url", "")
            link = f"https://www.courtlistener.com{absolute_url}"
            docket = item.get("docket_number", "")
            citation = item.get("citation", "")
            
            case_item = QTableWidgetItem(case_name)
            court_item = QTableWidgetItem(court)
            date_item = QTableWidgetItem(date_filed)
            url_item = QTableWidgetItem(link)
            url_item.setData(Qt.UserRole, link)
            docket_item = QTableWidgetItem(str(docket) if docket else "")
            
            if isinstance(citation, list):
                citation_str = ", ".join(str(c) for c in citation if c)
            else:
                citation_str = str(citation) if citation else ""
            citation_item = QTableWidgetItem(citation_str)
            
            self.results_table.setItem(row, 0, case_item)
            self.results_table.setItem(row, 1, court_item)
            self.results_table.setItem(row, 2, date_item)
            self.results_table.setItem(row, 3, url_item)
            self.results_table.setItem(row, 4, docket_item)
            self.results_table.setItem(row, 5, citation_item)

    def search_opinions(self):
        query = self.query_input.text()
        if not query:
            QMessageBox.warning(self, "Input Error", "Please enter a search query")
            return
            
        search_url = f"{API_BASE}/search/"
        params = {
            "q": query,
            "type": "o",
            "page_size": self.limit_spin.value(),
        }
        
        court_slug = self.court_combo.currentData()
        if court_slug:
            params["court"] = court_slug
            
        if self.use_date_range.isChecked():
            start_date = self.start_date.date().toString(Qt.ISODate)
            end_date = self.end_date.date().toString(Qt.ISODate)
            params["date_filed__gte"] = start_date
            params["date_filed__lte"] = end_date
            
        results = self.fetch_opinions(search_url, params)
        self.display_results(results)

    def fetch_current_opinions(self):
        search_url = f"{API_BASE}/opinions/"
        params = {
            "page_size": self.limit_spin.value(),
        }
        
        court_slug = self.court_combo.currentData()
        if court_slug:
            params["court__id"] = court_slug
            
        if self.use_date_range.isChecked():
            start_date = self.start_date.date().toString(Qt.ISODate)
            end_date = self.end_date.date().toString(Qt.ISODate)
            params["date_filed__gte"] = start_date
            params["date_filed__lte"] = end_date
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            params["date_filed__gte"] = today
            
        results = self.fetch_opinions(search_url, params)
        self.display_results(results)

    def export_results(self):
        if not self.search_results:
            QMessageBox.warning(self, "Export Error", "No results to export")
            return
            
        file_name, _ = QFileDialog.getSaveFileName(self, "Save CSV File", "", "CSV Files (*.csv)")
        if not file_name:
            return
            
        try:
            with open(file_name, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["case_name", "court", "date_filed", "url", "docket_number", "citation"],
                    extrasaction="ignore",
                )
                writer.writeheader()
                for item in self.search_results:
                    court = self.resolve_court_name(item.get("court"))
                    absolute_url = item.get("absolute_url", "")
                    url = f"https://www.courtlistener.com{absolute_url}"
                    citation = item.get("citation", "")
                    
                    if isinstance(citation, list):
                        citation_str = ", ".join(str(c) for c in citation if c)
                    else:
                        citation_str = str(citation) if citation else ""
                        
                    writer.writerow({
                        "case_name": item.get("case_name", "Unknown Case"),
                        "court": court,
                        "date_filed": item.get("date_filed", "Unknown Date"),
                        "url": url,
                        "docket_number": item.get("docket_number", ""),
                        "citation": citation_str,
                    })
            self.status_bar.showMessage(f"Results exported to {file_name}")
            QMessageBox.information(self, "Export Successful", f"Results exported to {file_name}")
        except IOError as e:
            self.status_bar.showMessage(f"Error writing to CSV: {e}")
            QMessageBox.critical(self, "Export Error", f"Error writing to CSV: {e}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = CourtListenerGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
