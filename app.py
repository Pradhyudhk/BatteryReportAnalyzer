import sys
import json
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QComboBox, QLabel, QTableWidget,
    QTableWidgetItem, QLineEdit, QHeaderView, QFileDialog
)
from PyQt5.QtCore import Qt
import numpy as np
from collections import defaultdict
from bs4 import BeautifulSoup
import re
import pyqtgraph as pg
from sklearn.linear_model import LinearRegression
import warnings
import calendar


class BatteryReportApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Battery Report Analyzer 🔋")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize with empty data
        self.battery_data = {
            "installed_batteries": {},
            "health_data": [],
            "usage_data": []
        }
        self.debug_log = []

        self.init_ui()
        self.load_styles()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Load Button
        load_button = QPushButton("📂 Load Battery Report")
        load_button.clicked.connect(self.load_report)
        load_button.setFixedWidth(150)
        main_layout.addWidget(load_button, alignment=Qt.AlignRight)

        # Tabs
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # Degradation Overview Tab
        degradation_tab = QWidget()
        degradation_layout = QVBoxLayout(degradation_tab)
        tabs.addTab(degradation_tab, "📉 Degradation")

        # Subtabs for Current and Insights
        degradation_subtabs = QTabWidget()
        degradation_layout.addWidget(degradation_subtabs)

        # Current Subtab
        current_tab = QWidget()
        current_layout = QVBoxLayout(current_tab)
        degradation_subtabs.addTab(current_tab, "📊 Current")

        # Period Selection
        period_layout = QHBoxLayout()
        period_label = QLabel("Group By:")
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Year", "Month", "Week"])
        self.period_combo.currentTextChanged.connect(self.update_degradation_periods)
        period_layout.addWidget(period_label)
        period_layout.addWidget(self.period_combo)

        self.year_combo = QComboBox()
        self.year_combo.currentTextChanged.connect(self.update_month_combo)
        period_layout.addWidget(self.year_combo)

        self.month_combo = QComboBox()
        self.month_combo.currentTextChanged.connect(self.update_week_combo)
        period_layout.addWidget(self.month_combo)

        self.week_combo = QComboBox()
        self.week_combo.currentTextChanged.connect(self.update_degradation_display)
        period_layout.addWidget(self.week_combo)

        period_layout.addStretch()
        current_layout.addLayout(period_layout)

        # Degradation Stats
        self.degradation_stats = QLabel()
        current_layout.addWidget(self.degradation_stats)

        # Specific Degradation
        self.specific_degradation_label = QLabel()
        current_layout.addWidget(self.specific_degradation_label)

        # Battery Health Table
        self.health_table = QTableWidget()
        self.health_table.setColumnCount(2)
        self.health_table.setHorizontalHeaderLabels(["Date", "Health (%)"])
        self.health_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.health_table.setSortingEnabled(True)
        current_layout.addWidget(self.health_table)

        # Insights Subtab
        insights_tab = QWidget()
        insights_layout = QVBoxLayout(insights_tab)
        degradation_subtabs.addTab(insights_tab, "💡 Insights")

        self.insights_label = QLabel()
        insights_layout.addWidget(self.insights_label)

        # Projections Tab
        projections_tab = QWidget()
        projections_layout = QVBoxLayout(projections_tab)
        tabs.addTab(projections_tab, "🔮 Projections")

        # Target Health Input and Predict Button
        target_layout = QHBoxLayout()
        target_label = QLabel("Target Health (%):")
        self.target_input = QLineEdit("80")
        predict_button = QPushButton("🔍 Predict Now")
        predict_button.clicked.connect(self.update_projections)
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_input)
        target_layout.addWidget(predict_button)
        target_layout.addStretch()
        projections_layout.addLayout(target_layout)

        # Prediction Result
        self.prediction_label = QLabel("Prediction: N/A")
        projections_layout.addWidget(self.prediction_label)

        # Graph
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle("Battery Health Over Time")
        self.plot_widget.setLabel('left', 'Health (%)')
        self.plot_widget.setLabel('bottom', 'Date')
        projections_layout.addWidget(self.plot_widget)

        # Battery Info Tab
        battery_info_tab = QWidget()
        battery_info_layout = QVBoxLayout(battery_info_tab)
        tabs.addTab(battery_info_tab, "🔧 Battery Info")

        self.battery_info_label = QLabel()
        battery_info_layout.addWidget(self.battery_info_label)

        search_button = QPushButton("🔎 Search for Replacements")
        search_button.clicked.connect(self.search_replacements)
        battery_info_layout.addWidget(search_button)

        # Usage Tab
        usage_tab = QWidget()
        usage_layout = QVBoxLayout(usage_tab)
        tabs.addTab(usage_tab, "⏰ Usage")

        # Usage Period Selection
        usage_period_layout = QHBoxLayout()
        usage_period_label = QLabel("Group By:")
        self.usage_period_combo = QComboBox()
        self.usage_period_combo.addItems(["Year", "Month", "Week"])
        self.usage_period_combo.currentTextChanged.connect(self.update_usage_periods)
        usage_period_layout.addWidget(usage_period_label)
        usage_period_layout.addWidget(self.usage_period_combo)

        self.usage_year_combo = QComboBox()
        self.usage_year_combo.currentTextChanged.connect(self.update_usage_month_combo)
        usage_period_layout.addWidget(self.usage_year_combo)

        self.usage_month_combo = QComboBox()
        self.usage_month_combo.currentTextChanged.connect(self.update_usage_week_combo)
        usage_period_layout.addWidget(self.usage_month_combo)

        self.usage_week_combo = QComboBox()
        self.usage_week_combo.currentTextChanged.connect(self.update_usage)
        usage_period_layout.addWidget(self.usage_week_combo)

        usage_period_layout.addStretch()
        usage_layout.addLayout(usage_period_layout)

        self.usage_label = QLabel()
        usage_layout.addWidget(self.usage_label)

        # Correlation Analysis
        self.correlation_label = QLabel()
        usage_layout.addWidget(self.correlation_label)

        # Debug Log Display
        self.debug_label = QLabel()
        usage_layout.addWidget(self.debug_label)

        # Initial Updates
        self.update_degradation_periods()
        self.update_usage_periods()
        self.update_insights()
        self.update_battery_info()
        self.update_usage()
        self.update_projections()

    def load_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QPushButton {
                background-color: #0078d4;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #005a9e; }
            QTabWidget::pane { border: 1px solid #d0d0d0; }
            QTabBar::tab {
                background: #e0e0e0;
                padding: 10px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border: 1px solid #d0d0d0;
                border-bottom: none;
            }
            QTableWidget {
                border: 1px solid #d0d0d0;
                background-color: white;
            }
            QTableWidget::item { padding: 5px; }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 5px;
                border: 1px solid #d0d0d0;
            }
            QComboBox, QLineEdit {
                padding: 5px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-size: 14px;
            }
            QLabel { font-size: 14px; }
        """)

    def load_report(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Battery Report", "", "HTML Files (*.html)")
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
        except Exception as e:
            self.degradation_stats.setText(f"⚠️ Error loading file: {str(e)}")
            return

        # Parse Installed Batteries
        battery_info = {}
        try:
            battery_section = soup.find(string=re.compile("Installed batteries", re.I)).find_next('table')
            if battery_section:
                rows = battery_section.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        key = cells[0].text.strip().lower().replace(' ', '_')
                        value = cells[1].text.strip()
                        if key in ['design_capacity', 'full_charge_capacity']:
                            value = int(re.sub(r'[^\d]', '', value)) if re.sub(r'[^\d]', '', value).isdigit() else 0
                        battery_info[key] = value
        except AttributeError:
            battery_info = {}
        self.battery_data["installed_batteries"] = battery_info

        # Parse Battery Capacity History
        health_data = []
        try:
            capacity_section = soup.find(string=re.compile("Battery capacity history", re.I)).find_next('table')
            if capacity_section:
                rows = capacity_section.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        period = cells[0].text.strip()
                        try:
                            full_charge = int(re.sub(r'[^\d]', '', cells[1].text.strip())) if re.sub(r'[^\d]', '',
                                                                                                     cells[
                                                                                                         1].text.strip()).isdigit() else 0
                            design_capacity = int(re.sub(r'[^\d]', '', cells[2].text.strip())) if re.sub(r'[^\d]', '',
                                                                                                         cells[
                                                                                                             2].text.strip()).isdigit() else 0
                            if design_capacity == 0:
                                continue
                            date_match = re.search(r'\d{4}-\d{2}-\d{2}$', period)
                            if date_match:
                                end_date = date_match.group(0)
                                date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                                health = (full_charge / design_capacity) * 100 if design_capacity else 0
                                health_data.append({
                                    "date": date_obj,
                                    "health": health
                                })
                        except (ValueError, AttributeError):
                            continue
        except AttributeError:
            health_data = []
        self.battery_data["health_data"] = sorted(health_data, key=lambda x: x["date"])
        self.debug_log.append(f"Health data entries: {len(self.battery_data['health_data'])}")
        if health_data:
            self.debug_log.append(
                f"Health data range: {health_data[0]['date'].strftime('%Y-%m-%d')} to {health_data[-1]['date'].strftime('%Y-%m-%d')}")
            self.debug_log.append(f"Health range: {health_data[0]['health']:.2f}% to {health_data[-1]['health']:.2f}%")

        # Parse Battery Usage
        usage_data = []
        try:
            usage_section = soup.find(string=re.compile("Battery usage", re.I)).find_next('table')
            if usage_section:
                rows = usage_section.find_all('tr')[1:]  
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        start_time = cells[0].text.strip()
                        state = cells[1].text.strip()
                        duration = cells[2].text.strip()
                        energy_drained = cells[3].text.strip()
                        if energy_drained != '-' and state in ['Active', 'Connected standby']:
                            try:
                                time_parts = list(map(int, duration.split(':')))
                                hours = time_parts[0] + time_parts[1] / 60 + time_parts[2] / 3600
                                if hours == 0:
                                    continue
                                date_obj = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                                usage_data.append({
                                    "date": date_obj,
                                    "hours_used": hours
                                })
                            except (ValueError, AttributeError):
                                continue
        except AttributeError:
            usage_data = []
        self.battery_data["usage_data"] = sorted(usage_data, key=lambda x: x["date"])
        self.debug_log.append(f"Usage data entries: {len(self.battery_data['usage_data'])}")
        if usage_data:
            self.debug_log.append(
                f"Usage data range: {usage_data[0]['date'].strftime('%Y-%m-%d %H:%M:%S')} to {usage_data[-1]['date'].strftime('%Y-%m-%d %H:%M:%S')}")

        # Display debug log in UI
        self.debug_label.setText("📋 Debug Log:\n" + "\n".join(self.debug_log))

        # UI
        self.update_degradation_periods()
        self.update_usage_periods()
        self.update_insights()
        self.update_battery_info()
        self.update_usage()
        self.update_projections()

    def get_week_range(self, year, month, week_num):
        first_day = datetime(year, month, 1)
        days_to_monday = (7 - first_day.weekday()) % 7
        if days_to_monday == 0:
            days_to_monday = 7
        start_date = first_day + timedelta(days=days_to_monday * (week_num - 1))
        end_date = start_date + timedelta(days=6)
        last_day = calendar.monthrange(year, month)[1]
        end_date = min(end_date, datetime(year, month, last_day))
        return start_date, end_date

    def update_degradation_periods(self):
        health_data = self.battery_data["health_data"]
        self.year_combo.clear()
        self.month_combo.clear()
        self.week_combo.clear()

        if not health_data:
            return

        years = sorted(set(d["date"].year for d in health_data))
        self.year_combo.addItems([str(y) for y in years])
        self.update_month_combo()

    def update_month_combo(self):
        health_data = self.battery_data["health_data"]
        self.month_combo.clear()
        self.week_combo.clear()

        if not health_data or not self.year_combo.currentText():
            return

        selected_year = int(self.year_combo.currentText())
        months = sorted(set(d["date"].month for d in health_data if d["date"].year == selected_year))
        self.month_combo.addItems([f"{datetime(2023, m, 1).strftime('%B')} {selected_year}" for m in months])
        self.update_week_combo()

    def update_week_combo(self):
        health_data = self.battery_data["health_data"]
        self.week_combo.clear()

        if not health_data or not self.month_combo.currentText():
            return

        selected_year = int(self.year_combo.currentText())
        selected_month = datetime.strptime(self.month_combo.currentText().split()[0], "%B").month
        first_day = datetime(selected_year, selected_month, 1)
        last_day = calendar.monthrange(selected_year, selected_month)[1]
        weeks = []
        current_date = first_day
        week_num = 1
        while current_date <= datetime(selected_year, selected_month, last_day):
            start_date, end_date = self.get_week_range(selected_year, selected_month, week_num)
            if start_date.month != selected_month:
                break
            weeks.append(f"Week {week_num}: {start_date.strftime('%d')}-{end_date.strftime('%d %b')}")
            current_date = end_date + timedelta(days=1)
            week_num += 1
        self.week_combo.addItems(weeks)
        self.update_degradation_display()

    def update_degradation_display(self):
        period = self.period_combo.currentText().lower()
        health_data = self.battery_data["health_data"]

        if not health_data:
            self.degradation_stats.setText("⚠️ No data available")
            self.health_table.setRowCount(0)
            self.specific_degradation_label.setText("⚠️ No period selected")
            return

        daily_degradations = []
        for i in range(1, len(health_data)):
            prev_health = health_data[i - 1]["health"]
            curr_health = health_data[i]["health"]
            degradation = prev_health - curr_health
            date_start = health_data[i - 1]["date"]
            date_end = health_data[i]["date"]
            days = (date_end - date_start).days
            if days > 0:
                daily_deg = degradation / days
                for d in range(days):
                    current_date = date_start + timedelta(days=d)
                    daily_degradations.append({"date": current_date, "degradation": daily_deg})

        if not daily_degradations:
            self.degradation_stats.setText("⚠️ No degradation data available")
            self.specific_degradation_label.setText("⚠️ No degradation data available")
            return

        weekly_degs = defaultdict(float)
        monthly_degs = defaultdict(float)
        yearly_degs = defaultdict(float)

        for deg in daily_degradations:
            date = deg["date"]
            degradation = deg["degradation"]
            year = date.year
            month = date.month
            first_day = datetime(year, month, 1)
            days_to_monday = (7 - first_day.weekday()) % 7
            if days_to_monday == 0:
                days_to_monday = 7
            day_of_month = date.day
            week_num = ((day_of_month - 1) + days_to_monday) // 7 + 1
            week_key = f"{year}-{month:02d}-W{week_num}"
            monthly_key = f"{year}-{month:02d}"
            yearly_key = str(year)

            weekly_degs[week_key] += degradation
            monthly_degs[monthly_key] += degradation
            yearly_degs[yearly_key] += degradation

        most_degraded_week = max(weekly_degs.items(), key=lambda x: x[1], default=("N/A", 0))
        least_degraded_week = min(weekly_degs.items(), key=lambda x: x[1], default=("N/A", 0))
        most_degraded_month = max(monthly_degs.items(), key=lambda x: x[1], default=("N/A", 0))
        least_degraded_month = min(monthly_degs.items(), key=lambda x: x[1], default=("N/A", 0))
        most_degraded_year = max(yearly_degs.items(), key=lambda x: x[1], default=("N/A", 0))
        least_degraded_year = min(yearly_degs.items(), key=lambda x: x[1], default=("N/A", 0))

        stats_text = (
            f"📈 Most Degraded Week: {most_degraded_week[0]} ({most_degraded_week[1]:.2f}%)\n"
            f"📉 Least Degraded Week: {least_degraded_week[0]} ({least_degraded_week[1]:.2f}%)\n"
            f"📈 Most Degraded Month: {most_degraded_month[0]} ({most_degraded_month[1]:.2f}%)\n"
            f"📉 Least Degraded Month: {least_degraded_month[0]} ({least_degraded_month[1]:.2f}%)\n"
            f"📈 Most Degraded Year: {most_degraded_year[0]} ({most_degraded_year[1]:.2f}%)\n"
            f"📉 Least Degraded Year: {least_degraded_year[0]} ({least_degraded_year[1]:.2f}%)"
        )
        self.degradation_stats.setText(stats_text)

        selected_year = self.year_combo.currentText()
        selected_month = self.month_combo.currentText()
        selected_week = self.week_combo.currentText()

        if not selected_year:
            self.specific_degradation_label.setText("⚠️ Please select a year")
            return

        selected_year = int(selected_year)
        if period == "year":
            total_deg = yearly_degs.get(str(selected_year), 0)
            self.specific_degradation_label.setText(f"🔍 Degradation in {selected_year}: {total_deg:.2f}%")
        elif period == "month" and selected_month:
            selected_month_num = datetime.strptime(selected_month.split()[0], "%B").month
            month_key = f"{selected_year}-{selected_month_num:02d}"
            total_deg = monthly_degs.get(month_key, 0)
            self.specific_degradation_label.setText(f"🔍 Degradation in {selected_month}: {total_deg:.2f}%")
        elif period == "week" and selected_month and selected_week:
            selected_month_num = datetime.strptime(selected_month.split()[0], "%B").month
            week_num = int(selected_week.split()[1].split(':')[0])
            week_key = f"{selected_year}-{selected_month_num:02d}-W{week_num}"
            total_deg = weekly_degs.get(week_key, 0)
            self.specific_degradation_label.setText(
                f"🔍 Degradation in {selected_month}, {selected_week}: {total_deg:.2f}%")
        else:
            self.specific_degradation_label.setText("⚠️ Please select a period")

        self.health_table.setRowCount(len(health_data))
        for i, entry in enumerate(health_data):
            self.health_table.setItem(i, 0, QTableWidgetItem(entry["date"].strftime("%Y-%m-%d")))
            self.health_table.setItem(i, 1, QTableWidgetItem(f"{entry['health']:.2f}"))

    def update_usage_periods(self):
        usage_data = self.battery_data["usage_data"]
        self.usage_year_combo.clear()
        self.usage_month_combo.clear()
        self.usage_week_combo.clear()

        if not usage_data:
            return

        years = sorted(set(d["date"].year for d in usage_data))
        if not years:
            self.usage_year_combo.addItem("No usage years available")
        else:
            self.usage_year_combo.addItems([str(y) for y in years])
        self.update_usage_month_combo()

    def update_usage_month_combo(self):
        usage_data = self.battery_data["usage_data"]
        self.usage_month_combo.clear()
        self.usage_week_combo.clear()

        if not usage_data or not self.usage_year_combo.currentText() or "No usage years" in self.usage_year_combo.currentText():
            return

        selected_year = int(self.usage_year_combo.currentText())
        months = sorted(set(d["date"].month for d in usage_data if d["date"].year == selected_year))
        if not months:
            self.usage_month_combo.addItem("No months available")
        else:
            self.usage_month_combo.addItems([f"{datetime(2023, m, 1).strftime('%B')} {selected_year}" for m in months])
        self.update_usage_week_combo()

    def update_usage_week_combo(self):
        usage_data = self.battery_data["usage_data"]
        self.usage_week_combo.clear()

        if not usage_data or not self.usage_month_combo.currentText() or "No months" in self.usage_month_combo.currentText():
            return

        selected_year = int(self.usage_year_combo.currentText())
        selected_month = datetime.strptime(self.usage_month_combo.currentText().split()[0], "%B").month
        first_day = datetime(selected_year, selected_month, 1)
        last_day = calendar.monthrange(selected_year, selected_month)[1]
        weeks = []
        current_date = first_day
        week_num = 1
        while current_date <= datetime(selected_year, selected_month, last_day):
            start_date, end_date = self.get_week_range(selected_year, selected_month, week_num)
            if start_date.month != selected_month:
                break
            weeks.append(f"Week {week_num}: {start_date.strftime('%d')}-{end_date.strftime('%d %b')}")
            current_date = end_date + timedelta(days=1)
            week_num += 1
        if not weeks:
            self.usage_week_combo.addItem("No weeks available")
        else:
            self.usage_week_combo.addItems(weeks)
        self.update_usage()

    def update_usage(self):
        usage_data = self.battery_data["usage_data"]
        health_data = self.battery_data["health_data"]

        if not usage_data:
            self.usage_label.setText("⚠️ No usage data available")
            self.correlation_label.setText("⚠️ No correlation data available")
            return

        weekly_usage = defaultdict(float)
        monthly_usage = defaultdict(float)
        yearly_usage = defaultdict(float)

        for entry in usage_data:
            date = entry["date"]
            hours = entry["hours_used"]
            year = date.year
            month = date.month
            first_day = datetime(year, month, 1)
            days_to_monday = (7 - first_day.weekday()) % 7
            if days_to_monday == 0:
                days_to_monday = 7
            day_of_month = date.day
            week_num = ((day_of_month - 1) + days_to_monday) // 7 + 1
            week_key = f"{year}-{month:02d}-W{week_num}"
            monthly_key = f"{year}-{month:02d}"
            yearly_key = str(year)

            weekly_usage[week_key] += hours
            monthly_usage[monthly_key] += hours
            yearly_usage[yearly_key] += hours

        most_used_week = max(weekly_usage.items(), key=lambda x: x[1], default=("N/A", 0))
        least_used_week = min(weekly_usage.items(), key=lambda x: x[1], default=("N/A", 0))
        most_used_month = max(monthly_usage.items(), key=lambda x: x[1], default=("N/A", 0))
        least_used_month = min(monthly_usage.items(), key=lambda x: x[1], default=("N/A", 0))
        most_used_year = max(yearly_usage.items(), key=lambda x: x[1], default=("N/A", 0))
        least_used_year = min(yearly_usage.items(), key=lambda x: x[1], default=("N/A", 0))

        def format_time(hours):
            if hours < 1:
                minutes = hours * 60
                return f"{minutes:.1f} min"
            return f"{hours:.2f} hr"

        period = self.usage_period_combo.currentText().lower()
        selected_year = self.usage_year_combo.currentText()
        selected_month = self.usage_month_combo.currentText()
        selected_week = self.usage_week_combo.currentText()

        usage_text = "⏰ Battery Usage (Time on Battery):\n\n"
        usage_text += f"📈 Most Used Week: {most_used_week[0]} ({format_time(most_used_week[1])})\n"
        usage_text += f"📉 Least Used Week: {least_used_week[0]} ({format_time(least_used_week[1])})\n"
        usage_text += f"📈 Most Used Month: {most_used_month[0]} ({format_time(most_used_month[1])})\n"
        usage_text += f"📉 Least Used Month: {least_used_month[0]} ({format_time(least_used_month[1])})\n"
        usage_text += f"📈 Most Used Year: {most_used_year[0]} ({format_time(most_used_year[1])})\n"
        usage_text += f"📉 Least Used Year: {least_used_year[0]} ({format_time(least_used_year[1])})\n\n"

        if not selected_year or "No usage years" in selected_year:
            usage_text += "⚠️ No usage years available"
        elif period == "year":
            total_hours = yearly_usage.get(selected_year, 0)
            usage_text += f"🔍 Usage in {selected_year}: {format_time(total_hours)}"
        elif period == "month" and selected_month and "No months" not in selected_month:
            selected_month_num = datetime.strptime(selected_month.split()[0], "%B").month
            month_key = f"{selected_year}-{selected_month_num:02d}"
            total_hours = monthly_usage.get(month_key, 0)
            usage_text += f"🔍 Usage in {selected_month}: {format_time(total_hours)}"
        elif period == "week" and selected_month and selected_week and "No weeks" not in selected_week:
            selected_month_num = datetime.strptime(selected_month.split()[0], "%B").month
            week_num = int(selected_week.split()[1].split(':')[0])
            week_key = f"{selected_year}-{selected_month_num:02d}-W{week_num}"
            total_hours = weekly_usage.get(week_key, 0)
            usage_text += f"🔍 Usage in {selected_month}, {selected_week}: {format_time(total_hours)}"
        else:
            usage_text += "⚠️ Please select a period"

        self.usage_label.setText(usage_text)

        if not health_data or not usage_data:
            self.correlation_label.setText("⚠️ No correlation data available")
            return

        weekly_degs = defaultdict(float)
        for i in range(1, len(health_data)):
            prev_health = health_data[i - 1]["health"]
            curr_health = health_data[i]["health"]
            degradation = prev_health - curr_health
            date_start = health_data[i - 1]["date"]
            date_end = health_data[i]["date"]
            days = (date_end - date_start).days
            if days > 0:
                daily_deg = degradation / days
                for d in range(days):
                    current_date = date_start + timedelta(days=d)
                    year = current_date.year
                    month = current_date.month
                    first_day = datetime(year, month, 1)
                    days_to_monday = (7 - first_day.weekday()) % 7
                    if days_to_monday == 0:
                        days_to_monday = 7
                    day_of_month = current_date.day
                    week_num = ((day_of_month - 1) + days_to_monday) // 7 + 1
                    week_key = f"{year}-{month:02d}-W{week_num}"
                    weekly_degs[week_key] += daily_deg

        deg_values = []
        usage_values = []
        for week_key in weekly_degs:
            if week_key in weekly_usage:
                deg_values.append(weekly_degs[week_key])
                usage_values.append(weekly_usage[week_key])

        if len(deg_values) < 2:
            self.correlation_label.setText("⚠️ Insufficient paired data for correlation analysis")
            return

        correlation = np.corrcoef(deg_values, usage_values)[0, 1]
        correlation_text = (
            f"📊 Correlation Analysis:\n"
            f"Pearson Correlation between Weekly Degradation and Usage Hours: {correlation:.2f}\n"
        )
        if correlation > 0.5:
            correlation_text += "Strong positive correlation: Higher usage hours are associated with more degradation.\n"
        elif correlation < -0.5:
            correlation_text += "Strong negative correlation: Higher usage hours are associated with less degradation.\n"
        else:
            correlation_text += "Weak or no correlation: Usage hours and degradation may not be directly related.\n"

        correlation_text += (
            "🔍 Causation Insights:\n"
            "Correlation does not imply causation. However, possible reasons for the observed relationship:\n"
            "- High usage may lead to more charge cycles, accelerating chemical degradation.\n"
            "- Low usage might indicate the battery was often plugged in, potentially causing overcharging stress.\n"
            "- External factors like temperature, charging habits, or battery age also influence degradation.\n"
        )
        self.correlation_label.setText(correlation_text)

    def update_insights(self):
        health_data = self.battery_data["health_data"]
        if not health_data:
            self.insights_label.setText("⚠️ No data available")
            return

        degradations = []
        for i in range(1, len(health_data)):
            degradation = health_data[i - 1]["health"] - health_data[i]["health"]
            date = health_data[i]["date"].strftime("%Y-%m-%d")
            degradations.append({"date": date, "degradation": degradation})

        deg_values = [d["degradation"] for d in degradations]
        median_deg = np.median(deg_values) if deg_values else 0

        high_deg_weeks = [d["date"] for d in degradations if d["degradation"] > median_deg]

        insights_text = f"💡 Weeks with degradation above median ({median_deg:.2f}%):\n"
        insights_text += "\n".join(high_deg_weeks) if high_deg_weeks else "None"
        self.insights_label.setText(insights_text)

    def update_projections(self):
        health_data = self.battery_data["health_data"]
        self.plot_widget.clear()

        if not health_data:
            self.prediction_label.setText("⚠️ Prediction: No data available")
            return

        dates = [entry["date"] for entry in health_data]
        healths = [entry["health"] for entry in health_data]
        timestamps = [d.timestamp() for d in dates]

        self.plot_widget.plot(timestamps, healths, pen=pg.mkPen('b', width=2), symbol='o')

        try:
            target = float(self.target_input.text())
            if not 0 <= target <= 100:
                raise ValueError("Target health must be between 0 and 100")

            if len(health_data) >= 2:
                X = np.array(timestamps).reshape(-1, 1)
                y = np.array(healths)
                model = LinearRegression()
                model.fit(X, y)

                latest_health = healths[-1]
                if model.coef_[0] < 0:
                    days_to_target = (latest_health - target) / (-model.coef_[0] * 86400)
                    predicted_date = dates[-1] + timedelta(days=days_to_target)

                    future_timestamp = predicted_date.timestamp()
                    self.plot_widget.plot([timestamps[-1], future_timestamp], [latest_health, target],
                                          pen=pg.mkPen('r', width=2, style=Qt.DashLine))

                    self.prediction_label.setText(
                        f"🔮 Prediction: Reach {target:.2f}% on {predicted_date.strftime('%Y-%m-%d')}")
                else:
                    self.prediction_label.setText("🔮 Prediction: Battery health not degrading")
            else:
                self.prediction_label.setText("⚠️ Prediction: Insufficient data for projection")
        except ValueError as e:
            self.prediction_label.setText(f"⚠️ Prediction: Invalid target ({str(e)})")

        self.plot_widget.getAxis('bottom').setTicks([[(t, d.strftime('%Y-%m-%d')) for t, d in zip(timestamps, dates)]])

    def update_battery_info(self):
        info = self.battery_data["installed_batteries"]
        if not info:
            self.battery_info_label.setText("⚠️ No battery info available")
            return
        info_text = (
            f"🏭 Manufacturer: {info.get('manufacturer', 'N/A')}\n"
            f"📜 Model Name: {info.get('name', 'N/A')}\n"
            f"🔢 Serial Number: {info.get('serial_number', 'N/A')}\n"
            f"⚡ Design Capacity: {info.get('design_capacity', 'N/A')} mWh"
        )
        self.battery_info_label.setText(info_text)

    def search_replacements(self):
        model = self.battery_data["installed_batteries"].get("name", "")
        if model:
            import webbrowser
            webbrowser.open(f"https://www.batterylookup.com/search?q={model}")


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    app = QApplication(sys.argv)
    window = BatteryReportApp()
    window.show()
    sys.exit(app.exec_())
