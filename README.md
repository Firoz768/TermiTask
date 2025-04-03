# Task Manager CLI Documentation

## 1. Overview

A command-line application for managing tasks with collaboration features and productivity tracking.

### Key Features

- Create, update, and delete tasks
- User authentication system
- Task assignment between team members
- Due dates and recurring reminders
- Tagging and advanced filtering
- Productivity reports with visual charts
- Data export/import functionality
- Customizable interface themes

## 2. Installation

### Requirements

- Python 3.8+
- Install dependencies:

```sh
pip install click bcrypt sqlite3 pandas matplotlib schedule
```

### Quick Start

```sh
python cli.py [command] [options]
```

## 3. Command Reference

### User Accounts

#### Register new user:

```sh
python cli.py register [Username] [Email] [Password]
```
(Password must be 8+ characters)

#### User login: 

```sh
python cli.py login [Username] [Password]
```

### Task Management

#### Add new task:

```sh
python cli.py add "Task Title" [options]
```

Options include:

- `--description "Task details"`
- `--due-date YYYY-MM-DD`
- `--priority low/medium/high/critical`
- `--tag work` (can use multiple times)
- `--recurrence daily/weekly/monthly`
- `--created-by username` (required)
- `--assign-to teammate`

#### List tasks:

```sh
python cli.py list [options]
```

Filter using:

- `--username filter_user`
- `--priority high`
- `--status pending/completed`
- `--overdue` (show only late tasks)
- `--search "keyword"`
- `--tag urgent`
- `--sort due_date/priority/created_at`
- `--reverse` (reverse sort order)

#### Update task:

```sh
python cli.py update [options]
```

#### Delete task:

```sh
python cli.py delete [Task_id]
```

### Team Features

#### Assign task:

```sh
python cli.py assign [Task_id] [assigner_username] [assignee_username]
```

#### Workload report:

```sh
python cli.py workload [Username]
```

### Data Operations

#### Productivity report:

```sh
python cli.py report [Username] --output chart.png
```

#### Export tasks:

```sh
python cli.py export tasks.csv
```

#### Backup data:

```sh
python cli.py backup backup_file.db
```

#### Restore data:

```sh
python cli.py restore backup_file.db
```

### Settings

#### Configure preferences:

```sh
python cli.py settings [options]
```

Options:

- `--theme light/dark`
- `--date-format "%Y-%m-%d"`
- `--notifications/--no-notifications`

## 4. Common Issues

### Task ID errors:

- Use full 36-character task IDs
- Example: `550e8400-e29b-41d4-a716-446655440000`

### Date format:

- Always use `YYYY-MM-DD` format
- Example: `2024-12-31`

### Debug mode:

Add `--verbose` flag to any command for detailed logs:

```sh
python cli.py --verbose list --overdue
```

### Generate weekly report:

```sh
python cli.py report team_lead --output weekly.png
```

### Export for backup:

```sh
python cli.py [Filename].csv
