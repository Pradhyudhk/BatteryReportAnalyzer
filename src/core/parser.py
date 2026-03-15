import re
from datetime import datetime
from bs4 import BeautifulSoup

def parse_battery_report(file_path):
    battery_data = {
        "installed_batteries": {},
        "health_data": [],
        "usage_data": []
    }
    debug_log = []

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
    except Exception as e:
        raise Exception(f"Error loading file: {str(e)}")

    # Parse Installed Batteries
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
                    battery_data["installed_batteries"][key] = value
    except AttributeError:
        pass

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
                        full_charge = int(re.sub(r'[^\d]', '', cells[1].text.strip())) if re.sub(r'[^\d]', '', cells[1].text.strip()).isdigit() else 0
                        design_capacity = int(re.sub(r'[^\d]', '', cells[2].text.strip())) if re.sub(r'[^\d]', '', cells[2].text.strip()).isdigit() else 0
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
        pass
    battery_data["health_data"] = sorted(health_data, key=lambda x: x["date"])
    debug_log.append(f"Health data entries: {len(battery_data['health_data'])}")
    if health_data:
        debug_log.append(
            f"Health data range: {health_data[0]['date'].strftime('%Y-%m-%d')} to {health_data[-1]['date'].strftime('%Y-%m-%d')}")
        debug_log.append(f"Health range: {health_data[0]['health']:.2f}% to {health_data[-1]['health']:.2f}%")

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
        pass
    battery_data["usage_data"] = sorted(usage_data, key=lambda x: x["date"])
    debug_log.append(f"Usage data entries: {len(battery_data['usage_data'])}")
    if usage_data:
        debug_log.append(
            f"Usage data range: {usage_data[0]['date'].strftime('%Y-%m-%d %H:%M:%S')} to {usage_data[-1]['date'].strftime('%Y-%m-%d %H:%M:%S')}")

    return battery_data, debug_log
