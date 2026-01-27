INTENTS = [
    "OPEN_MODULE",
    "BUILD_REPORT",
    "OPEN_FORM",
    "CONFIGURE_MODULE",
    "SHOW_DATA",
    "EXPORT_DATA",
    "IMPORT_DATA",
    "SHOW_SYSTEM_INFO",
    "ADMIN_ACTION",
    "UNKNOWN"
]

DICTIONARY = {
    "WELL_FIELD": "месторождение",
    "WELL_NAME": "скважина"
}

# В models/constants.py добавьте или обновите эти константы:

WELL_FIELDS = [
    "Самотлор", "Приобское", "Ванкор", "Вишанское", "Уренгойское",
    "Ямбургское", "Бованенково", "Юрубчено", "Чаяндинское",
    "Покачевское", "Русское", "Западно-Малобалыкское",  # Добавлены новые
    "Вынгаяхинское", "Медвежье", "Губкинское"
]

WELL_NAMES = [
    "123А", "17Б", "45", "102Г", "56В", "89Д", "201А", "345",
    "850", "951", "105", "207", "309", "401", "503",
    "605", "707", "809", "911", "1012"
]

PERIODS = [
    "январь", "февраль", "март", "апрель", "май", 
    "июнь", "июль", "август", "сентябрь", "октябрь", 
    "ноябрь", "декабрь",
    "текущий месяц", "прошлый месяц", "следующий месяц",
    "предыдущий месяц", "этот месяц"
]

REPORT_NAME = ["по данным", "данные"]

FORM_TYPES = [
    "ввода данных",
    "регистрации",
    "редактирования",
    "карточка скважины",
    "карточка объекта"
]

NER_LABELS = [
    "O", 
    "B-TARGET", 
    "I-TARGET", 
    "B-WELL_FIELD", 
    "I-WELL_FIELD", 
    "B-WELL_NAME", 
    "I-WELL_NAME", 
    "B-PERIOD", 
    "I-PERIOD", 
    "B-REPORT_NAME", 
    "I-REPORT_NAME",
    "B-DATE", 
    "I-DATE",
    "B-MONTH", 
    "I-MONTH",
    "B-YEAR", 
    "I-YEAR"
]

PERIODS = [
    "январь", "февраль", "март", "апрель", "май", 
    "июнь", "июль", "август", "сентябрь", "октябрь", 
    "ноябрь", "декабрь",
    "текущий месяц", "прошлый месяц", "следующий месяц",
    "предыдущий месяц", "этот месяц", "последний месяц"
]

SPECIAL_PERIODS = [
    "текущий месяц",
    "прошлый месяц", 
    "предыдущий месяц",
    "последний месяц",
    "следующий месяц",
    "этот месяц"
]
DATES = [
    "1 января", "15 января", "31 января",
    "5 февраля", "20 февраля",
    "10 марта", "25 марта",
    "1 апреля", "15 апреля", "30 апреля",
    "5 мая", "20 мая",
    "10 июня", "25 июня",
    "1 июля", "15 июля", "31 июля",
    "5 августа", "20 августа",
    "10 сентября", "25 сентября",
    "1 октября", "15 октября", "31 октября",
    "5 ноября", "20 ноября",
    "10 декабря", "25 декабря",
    "первое января", "пятнадцатое января", "тридцать первое января",
    "первое февраля", "пятнадцатое февраля",
    "десятое марта", "двадцать пятое марта",
    "первое апреля", "пятнадцатое апреля", "тридцатое апреля",
    "первое мая", "пятнадцатое мая",
    "десятое июня", "двадцать пятое июня",
    "первое июля", "пятнадцатое июля", "тридцать первое июля",
    "первое августа", "пятнадцатое августа",
    "десятое сентября", "двадцать пятое сентября",
    "первое октября", "пятнадцатое октября", "тридцать первое октября",
    "первое ноября", "пятнадцатое ноября",
    "десятое декабря", "двадцать пятое декабря",
    "1.01", "15.01", "31.01", "1.02", "15.02", "10.03", "25.03"
]

YEARS = [
    "2023 года", "2024 года", "2025 года", "2026 года", 
    "2023 г.", "2024 г.", "2025 г.", "2026 г.",
    "2023", "2024", "2025", "2026"
]

ner2id = {l: i for i, l in enumerate(NER_LABELS)}
id2ner = {i: l for l, i in ner2id.items()}

COMMAND_TEMPLATES = {
    "OPEN_MODULE": [
        ["Открой", "{TARGET}"],
        ["Покажи", "{TARGET}"],
        ["Запусти", "{TARGET}"],
        ["Открой", "{TARGET}", "по"],
        ["Покажи", "{TARGET}", "для"],
        ["{TARGET}"],
    ],

    "BUILD_REPORT": [
        ["Построй", "{TARGET}"],
        ["Сформируй", "{TARGET}"],
        ["Сделай", "{TARGET}"],
        ["Подготовь", "{TARGET}"],
        ["Создай", "{TARGET}"],
        ["Выведи", "{TARGET}"],
        ["Покажи", "{TARGET}"],
        ["Сгенерируй", "{TARGET}"]
    ],

    "OPEN_FORM": [
        ["Открой", "форму", "{TARGET}"],
        ["Покажи", "форму", "{TARGET}"],
        ["Форма", "{TARGET}"],
    ],

    "RUN_QUERY": [
        ["Выполни", "запрос", "{TARGET}"],
        ["Запрос", "{TARGET}"],
    ],

    "CONFIGURE_MODULE": [
        ["Настрой", "{TARGET}"],
        ["Открой", "настройки", "{TARGET}"],
    ],

    "SHOW_DATA": [
        ["Покажи", "данные", "{TARGET}"],
        ["Отобрази", "{TARGET}"],
    ],

    "IMPORT_DATA": [
        ["Импортируй", "данные"],
        ["Загрузи", "данные"],
    ],

    "EXPORT_DATA": [
        ["Экспортируй", "данные"],
        ["Выгрузи", "данные"],
    ],

    "SHOW_SYSTEM_INFO": [
        ["Покажи", "{TARGET}"],
        ["Открой", "{TARGET}"],
        ["Информация", "{TARGET}"],
    ],

    "ADMIN_ACTION": [
        ["Управление", "{TARGET}"],
        ["Открой", "{TARGET}"],
    ],

}


TARGET_SYNONYMS = {
    "Ois.Modules.chessy.ChessyModule": ["шахматка", "шахматку"],
    "forms_input_engine": ["движок форм", "формы ввода", "движок форм ввода"],
    "reporting_engine": ["движок отчетности", "отчетность"],
    "wells_registry": ["реестр скважин", "реестр объектов", "реестр"],
    "nsi": ["нси", "нс и"],
    "fund_maintenance": ["ведение фонда", "фонд"],
    "run_stop_module": ["запуски-остановки", "запуски", "остановки"],
    "mode_output": ["вывод на режим", "режим"],
    "volume_balance": ["баланс объемов", "баланс"],
    "standalone_report": ["отчет", "отчёты", "сводка", "доклад", "аудит"],
    "well_construction": [
        "конструкция",
        "конструкцию",
        "конструкция скважины",
        "конструкцию скважины",
        "данные по конструкции",
        "схема конструкции",
        "схему конструкции"
    ],
    "annual_planning": ["годовое планирование", "планирование"],
    "wellhead_survey": ["обследование устьев", "устья скважин"],
    "technological_mode": ["технологический режим", "тех режим"],
    "measurements_verification": ["верификация замеров", "верификация"],
}

REGISTRY = {
    "Ois.Modules.chessy.ChessyModule": {
        "intent": "OPEN_MODULE",
        "target": "Ois.Modules.chessy.ChessyModule",
        "slots": {
            "WELL_FIELD": {"required": True},
            "WELL_NAME": {"required": True},
            "PERIOD": {"required": False}
        }
    },

    "forms_input_engine": {
        "intent": "OPEN_MODULE",
        "target": "forms_input_engine",
        "slots": {}
    },

    "reporting_engine": {
        "intent": "OPEN_MODULE",
        "target": "reporting_engine",
        "slots": {}
    },

    "wells_registry": {
        "intent": "OPEN_MODULE",
        "target": "wells_registry",
        "slots": {}
    },

    "nsi": {
        "intent": "OPEN_MODULE",
        "target": "nsi",
        "slots": {}
    },

    "fund_maintenance": {
        "intent": "OPEN_MODULE",
        "target": "fund_maintenance",
        "slots": {}
    },

    "run_stop_module": {
        "intent": "OPEN_MODULE",
        "target": "run_stop_module",
        "slots": {}
    },

    "mode_output": {
        "intent": "OPEN_MODULE",
        "target": "mode_output",
        "slots": {
            "WELL_FIELD": {"required": True},
            "WELL_NAME": {"required": True}
        }
    },

    "volume_balance": {
        "intent": "OPEN_MODULE",
        "target": "volume_balance",
        "slots": {}
    },

    "standalone_report": {
        "intent": "BUILD_REPORT",
        "target": "standalone_report",
        "slots": {
            "REPORT_NAME": {"required": True},
            "PERIOD": {"required": False}
        }
    },

    "well_construction": {
        "intent": "OPEN_MODULE",
        "target": "well_construction",
        "slots": {
            "WELL_FIELD": {"required": True},
            "WELL_NAME": {"required": True}
        }
    },

    "annual_planning": {
        "intent": "OPEN_MODULE",
        "target": "annual_planning",
        "slots": {}
    },

    "wellhead_survey": {
        "intent": "OPEN_MODULE",
        "target": "wellhead_survey",
        "slots": {
            "WELL_FIELD": {"required": True},
            "WELL_NAME": {"required": True}
        }
    },

    "technological_mode": {
        "intent": "OPEN_MODULE",
        "target": "technological_mode",
        "slots": {
            "WELL_FIELD": {"required": True},
            "WELL_NAME": {"required": True}
        }
    },

    "measurements_verification": {
        "intent": "OPEN_MODULE",
        "target": "measurements_verification",
        "slots": {}
    }
}