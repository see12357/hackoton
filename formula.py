import psycopg2
from psycopg2 import sql
from sympy import symbols, Eq, latex, sin, cos, pi, simplify, factorial, tan, cot, sec, csc, sqrt, ln, exp, integrate, Sum
from sympy.core.basic import Basic
import json
import hashlib
import re

def connect_to_db():
    """Устанавливает соединение с базой данных."""
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="admin",
            host="127.0.0.1",
            port="5432"
        )
        return conn
    except Exception as e:
        print("Ошибка подключения к базе данных:", e)
        return None

def parse_formula(expr):
    """Преобразует выражение SymPy в JSON-совместимую структуру."""
    try:
        def sympy_to_dict(expr):
            if isinstance(expr, Basic):
                return {
                    "type": type(expr).__name__,
                    "args": [sympy_to_dict(arg) for arg in expr.args]
                }
            elif isinstance(expr, (int, float, str)):
                return expr
            elif hasattr(expr, 'name'):  # Для символов
                return {"type": "Symbol", "name": expr.name}
            else:
                raise ValueError(f"Unsupported type: {type(expr)}")

        return json.dumps(sympy_to_dict(expr))
    except Exception as e:
        print("Ошибка при парсинге формулы:", e)
        return None

def remove_left_right(latex_string):
    """Удаляет \\left и \\right из LaTeX строки."""
    latex_string = re.sub(r"\\left\(", "(", latex_string)
    latex_string = re.sub(r"\\right\)", ")", latex_string)
    latex_string = re.sub(r"\\left\[", "[", latex_string)
    latex_string = re.sub(r"\\right\]", "]", latex_string)
    latex_string = re.sub(r"\\left\{", "{", latex_string)
    latex_string = re.sub(r"\\right\}", "}", latex_string)
    latex_string = re.sub(r"\\left\|", "|", latex_string)
    latex_string = re.sub(r"\\right\|", "|", latex_string)
    # Добавил обработку для других типов скобок и разделителей
    latex_string = re.sub(r"\\left\.", "", latex_string)  # Убираем \left.
    latex_string = re.sub(r"\\right\.", "", latex_string) # Убираем \right.
    return latex_string



def add_formula(conn, name, equation, formula_type, category=None, variables=None, tags=None):
    """Добавляет формулу в базу данных."""
    latex_string = latex(equation)
    latex_string = remove_left_right(latex_string)  # Удаляем left/right

    structure = parse_formula(equation)
    if structure is None:
        print("Не удалось добавить формулу: ошибка преобразования.")
        return None

    formula_hash = calculate_hash(equation)
    if formula_hash is None:
        print("Не удалось вычислить хэш формулы.")
        return None

    variables_json = json.dumps(variables) if variables else None
    tags_json = json.dumps(tags) if tags else None

    try:
        query_check = sql.SQL("""
            SELECT id FROM formulas WHERE formula_hash = %s;
        """)
        with conn.cursor() as cursor:
            cursor.execute(query_check, (formula_hash,))
            existing_formula = cursor.fetchone()
            if existing_formula:
                print(f"Формула с хэшем {formula_hash} уже существует с ID: {existing_formula[0]}")
                return existing_formula[0]

        query_insert = sql.SQL("""
            INSERT INTO formulas (name, latex, structure, formula_type, category, variables, formula_hash, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """)
        with conn.cursor() as cursor:
            cursor.execute(query_insert, (name, latex_string, structure, formula_type, category, variables_json, formula_hash, tags_json))
            conn.commit()
            formula_id = cursor.fetchone()[0]
            print(f"Формула добавлена с ID: {formula_id}")
            return formula_id
    except Exception as e:
        print("Ошибка при добавлении формулы в базу данных:", e)
        conn.rollback() # rollback чтобы не было частичных изменений
        return None

def calculate_hash(equation):
    """Вычисляет хэш формулы на основе её структуры."""
    structure = parse_formula(equation)
    if structure is not None:
        return hashlib.sha256(structure.encode('utf-8')).hexdigest()
    return None

def analyze_formula_structure(structure):
    if isinstance(structure, dict):
        return 1 + sum(analyze_formula_structure(arg) for arg in structure.get("args", []))
    return 0

def main():
    conn = connect_to_db()
    if conn is None:
        print("Не удалось подключиться к базе данных. Завершение программы.")
        return

        # Определение переменных для использования в формулах
    a, b, c, x, y, z, r, h, n, k, t, e, s, R, d1, d2, V, A, W, F, v, u, i = symbols(
        'a b c x y z r h n k t e s R d1 d2 V A W F v u i')
    P, S, d, l, alpha, beta, gamma, theta, q, m, PMT = symbols('P S d l alpha beta gamma theta q m PMT')

    # Список формул
    formulas = [
        # Комбинаторика
        {"name": "Рекуррентная формула факториала",
         "equation": Eq(factorial(n), n * factorial(n - 1)),
         "type": "mathematic",
         "category": "combinatorics",
         "variables": {"n": "number"}},
        {"name": "Число перестановок",
         "equation": Eq(factorial(n) / factorial(n - r), factorial(n) // factorial(n - r)),
         "type": "mathematic",
         "category": "permutations",
         "variables": {"n": "number", "r": "selection"}},
        {"name": "Число сочетаний",
         "equation": Eq(factorial(n) / (factorial(r) * factorial(n - r)),
                        factorial(n) // (factorial(r) * factorial(n - r))),
         "type": "mathematic",
         "category": "combinations",
         "variables": {"n": "number", "r": "selection"}},

        # Основные тригонометрические тождества
        {"name": "Основное тригонометрическое тождество",
         "equation": Eq(sin(alpha) ** 2 + cos(alpha) ** 2, 1),
         "type": "mathematic",
         "category": "trigonometry",
         "variables": {"alpha": "angle"}},
        {"name": "Тождество для тангенса",
         "equation": Eq(1 + tan(alpha) ** 2, sec(alpha) ** 2),
         "type": "mathematic",
         "category": "trigonometry",
         "variables": {"alpha": "angle"}},
        {"name": "Тождество для котангенса",
         "equation": Eq(1 + cot(alpha) ** 2, csc(alpha) ** 2),
         "type": "mathematic",
         "category": "trigonometry",
         "variables": {"alpha": "angle"}},

        # Формулы двойного аргумента
        {"name": "Формула синуса двойного угла",
         "equation": Eq(sin(2 * alpha), 2 * sin(alpha) * cos(alpha)),
         "type": "mathematic",
         "category": "trigonometry",
         "variables": {"alpha": "angle"}},
        {"name": "Формула косинуса двойного угла",
         "equation": Eq(cos(2 * alpha), cos(alpha) ** 2 - sin(alpha) ** 2),
         "type": "mathematic",
         "category": "trigonometry",
         "variables": {"alpha": "angle"}},
        {"name": "Формула тангенса двойного угла",
         "equation": Eq(tan(2 * alpha), 2 * tan(alpha) / (1 - tan(alpha) ** 2)),
         "type": "mathematic",
         "category": "trigonometry",
         "variables": {"alpha": "angle"}},

        # Формулы тройного аргумента
        {"name": "Формула синуса тройного угла",
         "equation": Eq(sin(3 * alpha), 3 * sin(alpha) - 4 * sin(alpha) ** 3),
         "type": "mathematic",
         "category": "trigonometry",
         "variables": {"alpha": "angle"}},
        {"name": "Формула косинуса тройного угла",
         "equation": Eq(cos(3 * alpha), 4 * cos(alpha) ** 3 - 3 * cos(alpha)),
         "type": "mathematic",
         "category": "trigonometry",
         "variables": {"alpha": "angle"}},

        # Формулы преобразования суммы (разности) в произведение
        {"name": "Формула преобразования суммы синусов в произведение",
         "equation": Eq(sin(alpha) + sin(beta), 2 * sin((alpha + beta) / 2) * cos((alpha - beta) / 2)),
         "type": "mathematic",
         "category": "trigonometry",
         "variables": {"alpha": "angle", "beta": "angle"}},
        {"name": "Формула преобразования разности синусов в произведение",
         "equation": Eq(sin(alpha) - sin(beta), 2 * cos((alpha + beta) / 2) * sin((alpha - beta) / 2)),
         "type": "mathematic",
         "category": "trigonometry",
         "variables": {"alpha": "angle", "beta": "angle"}},

        # Формулы преобразования произведения в сумму
        {"name": "Формула преобразования произведения синуса и косинуса в сумму",
         "equation": Eq(sin(alpha) * cos(beta), 0.5 * (sin(alpha + beta) + sin(alpha - beta))),
         "type": "mathematic",
         "category": "trigonometry",
         "variables": {"alpha": "angle", "beta": "angle"}},
        {"name": "Формула преобразования произведения косинусов в сумму",
         "equation": Eq(cos(alpha) * cos(beta), 0.5 * (cos(alpha + beta) + cos(alpha - beta))),
         "type": "mathematic",
         "category": "trigonometry",
         "variables": {"alpha": "angle", "beta": "angle"}},

        # Формулы половинного аргумента
        {"name": "Формула синуса половинного угла",
         "equation": Eq(sin(alpha / 2), sqrt((1 - cos(alpha)) / 2)),
         "type": "mathematic",
         "category": "trigonometry",
         "variables": {"alpha": "angle"}},
        {"name": "Формула косинуса половинного угла",
         "equation": Eq(cos(alpha / 2), sqrt((1 + cos(alpha)) / 2)),
         "type": "mathematic",
         "category": "trigonometry",
         "variables": {"alpha": "angle"}},

        # Уравнение окружности
        {"name": "Уравнение окружности",
         "equation": Eq((x - a) ** 2 + (y - b) ** 2, r ** 2),
         "type": "mathematic",
         "category": "geometry",
         "variables": {"x": "coordinate", "y": "coordinate", "a": "center_x", "b": "center_y", "r": "radius"}},

        # Прямая на плоскости
        {"name": "Уравнение прямой на плоскости",
         "equation": Eq(y, m * x + c),
         "type": "mathematic",
         "category": "geometry",
         "variables": {"m": "slope", "c": "y_intercept"}},
        {"name": "Наклон прямой на плоскости",
         "equation": Eq(m, (y - b) / (x - a)),
         "type": "mathematic",
         "category": "geometry",
         "variables": {"x": "x1", "y": "y1", "a": "x2", "b": "y2"}},

        # Пределы
        {"name": "Предел последовательности",
         "equation": Eq(simplify((1 + 1 / n) ** n), simplify(exp(1))),
         "type": "mathematic",
         "category": "limits",
         "variables": {"n": "number"}},

        # Основные правила дифференцирования
        {"name": "Производная степенной функции",
         "equation": Eq((x ** n).diff(x), n * x ** (n - 1)),
         "type": "mathematic",
         "category": "differentiation",
         "variables": {"x": "variable", "n": "exponent"}},
        {"name": "Производная синуса",
         "equation": Eq((sin(x)).diff(x), cos(x)),
         "type": "mathematic",
         "category": "differentiation",
         "variables": {"x": "variable"}},

        # Формулы дифференцирования
        {"name": "Производная натурального логарифма",
         "equation": Eq((ln(x)).diff(x), 1 / x),
         "type": "mathematic",
         "category": "differentiation",
         "variables": {"x": "variable"}},
        {"name": "Производная экспоненты",
         "equation": Eq((e ** x).diff(x), exp(x)),
         "type": "mathematic",
         "category": "differentiation",
         "variables": {"x": "variable"}},

        # Показательная и логарифмическая функции
        {"name": "Показательная функция через экспоненту",
         "equation": Eq(a ** x, exp(x * ln(a))),
         "type": "mathematic",
         "category": "exponential",
         "variables": {"a": "base", "x": "exponent"}},

        # Первообразная и интеграл
        {"name": "Интеграл степенной функции",
         "equation": Eq(simplify(integrate(x ** n, x)), x ** (n + 1) / (n + 1)),
         "type": "mathematic",
         "category": "integration",
         "variables": {"x": "variable", "n": "exponent"}},
        {"name": "Интеграл синуса",
         "equation": Eq(simplify(integrate(sin(x), x)), -cos(x)),
         "type": "mathematic",
         "category": "integration",
         "variables": {"x": "variable"}},

        # Треугольники
        {"name": "Площадь треугольника по формуле Герона",
         "equation": Eq(S, sqrt(s * (s - a) * (s - b) * (s - c))),
         "type": "mathematic",
         "category": "geometry",
         "variables": {"s": "semi_perimeter", "a": "side", "b": "side", "c": "side"}},

        # Формулы для радиусов вписанных и описанных окружностей правильных многоугольников
        {"name": "Радиус вписанной окружности правильного многоугольника",
         "equation": Eq(r, a / (2 * tan(pi / n))),
         "type": "mathematic",
         "category": "geometry",
         "variables": {"r": "inradius", "a": "side_length", "n": "number_of_sides"}},
        {"name": "Радиус описанной окружности правильного многоугольника",
         "equation": Eq(R, a / (2 * sin(pi / n))),
         "type": "mathematic",
         "category": "geometry",
         "variables": {"R": "circumradius", "a": "side_length", "n": "number_of_sides"}},

        # Четырехугольники
        {"name": "Площадь четырехугольника через диагонали и угол",
         "equation": Eq(S, 0.5 * d1 * d2 * sin(alpha)),
         "type": "mathematic",
         "category": "geometry",
         "variables": {"S": "area", "d1": "diagonal_1", "d2": "diagonal_2", "alpha": "angle_between_diagonals"}},

        # Многогранники
        {"name": "Объем куба",
         "equation": Eq(V, a ** 3),
         "type": "mathematic",
         "category": "geometry",
         "variables": {"V": "volume", "a": "side"}},
        {"name": "Площадь поверхности куба",
         "equation": Eq(S, 6 * a ** 2),
         "type": "mathematic",
         "category": "geometry",
         "variables": {"S": "surface_area", "a": "side"}},

        # Теорема Пифагора
        {"name": "Теорема Пифагора",
         "equation": Eq(a ** 2 + b ** 2, c ** 2),
         "type": "mathematic",
         "category": "geometry",
         "variables": {"a": "leg", "b": "leg", "c": "hypotenuse"}},

        # Длина окружности
        {"name": "Длина окружности",
         "equation": Eq(l, 2 * pi * r),
         "type": "mathematic",
         "category": "geometry",
         "variables": {"l": "circumference", "r": "radius"}},

        # Площадь круга
        {"name": "Площадь круга",
         "equation": Eq(S, pi * r ** 2),
         "type": "mathematic",
         "category": "geometry",
         "variables": {"S": "area", "r": "radius"}},

        # Объем шара
        {"name": "Объем шара",
         "equation": Eq(V, (4 / 3) * pi * r ** 3),
         "type": "mathematic",
         "category": "geometry",
         "variables": {"V": "volume", "r": "radius"}},

        # Площадь сферы
        {"name": "Площадь сферы",
         "equation": Eq(S, 4 * pi * r ** 2),
         "type": "mathematic",
         "category": "geometry",
         "variables": {"S": "surface_area", "r": "radius"}},

        # Логарифмы
        {"name": "Сумма логарифмов",
         "equation": Eq(ln(a * b), ln(a) + ln(b)),
         "type": "mathematic",
         "category": "logarithms",
         "variables": {"a": "value", "b": "value"}},
        {"name": "Разность логарифмов",
         "equation": Eq(ln(a / b), ln(a) - ln(b)),
         "type": "mathematic",
         "category": "logarithms",
         "variables": {"a": "value", "b": "value"}},

        # Производные
        {"name": "Производная косинуса",
         "equation": Eq((cos(x)).diff(x), -sin(x)),
         "type": "mathematic",
         "category": "differentiation",
         "variables": {"x": "variable"}},
        {"name": "Производная тангенса",
         "equation": Eq((tan(x)).diff(x), 1 / cos(x) ** 2),
         "type": "mathematic",
         "category": "differentiation",
         "variables": {"x": "variable"}},
        {"name": "Производная котангенса",
         "equation": Eq((cot(x)).diff(x), -1 / sin(x) ** 2),
         "type": "mathematic",
         "category": "differentiation",
         "variables": {"x": "variable"}},
        {"name": "Производная секанса",
         "equation": Eq((sec(x)).diff(x), sec(x) * tan(x)),
         "type": "mathematic",
         "category": "differentiation",
         "variables": {"x": "variable"}},
        {"name": "Производная косеканса",
         "equation": Eq((csc(x)).diff(x), -csc(x) * cot(x)),
         "type": "mathematic",
         "category": "differentiation",
         "variables": {"x": "variable"}},

        # Интегралы
        {"name": "Интеграл косинуса",
         "equation": Eq(simplify(integrate(cos(x), x)), sin(x)),
         "type": "mathematic",
         "category": "integration",
         "variables": {"x": "variable"}},
        {"name": "Интеграл тангенса",
         "equation": Eq(simplify(integrate(tan(x), x)), -ln(cos(x))),
         "type": "mathematic",
         "category": "integration",
         "variables": {"x": "variable"}},
        {"name": "Интеграл котангенса",
         "equation": Eq(simplify(integrate(cot(x), x)), ln(sin(x))),
         "type": "mathematic",
         "category": "integration",
         "variables": {"x": "variable"}},
        {"name": "Интеграл секанса",
         "equation": Eq(simplify(integrate(sec(x), x)), ln(sec(x) + tan(x))),
         "type": "mathematic",
         "category": "integration",
         "variables": {"x": "variable"}},
        {"name": "Интеграл косеканса",
         "equation": Eq(simplify(integrate(csc(x), x)), -ln(csc(x) + cot(x))),
         "type": "mathematic",
         "category": "integration",
         "variables": {"x": "variable"}},

        # Кинематика
        {"name": "Уравнение скорости",
         "equation": Eq(v, u + a * t),
         "type": "mathematic",
         "category": "kinematics",
         "variables": {"v": "final_velocity", "u": "initial_velocity", "a": "acceleration", "t": "time"}},
        {"name": "Уравнение перемещения",
         "equation": Eq(s, u * t + 0.5 * a * t ** 2),
         "type": "mathematic",
         "category": "kinematics",
         "variables": {"s": "displacement", "u": "initial_velocity", "a": "acceleration", "t": "time"}},
        {"name": "Уравнение движения",
         "equation": Eq(v ** 2, u ** 2 + 2 * a * s),
         "type": "mathematic",
         "category": "kinematics",
         "variables": {"v": "final_velocity", "u": "initial_velocity", "a": "acceleration", "s": "displacement"}},

        # Физика
        {"name": "Второй закон Ньютона",
         "equation": Eq(F, m * a),
         "type": "mathematic",
         "category": "physics",
         "variables": {"F": "force", "m": "mass", "a": "acceleration"}},
        {"name": "Работа силы",
         "equation": Eq(W, F * d * cos(theta)),
         "type": "mathematic",
         "category": "physics",
         "variables": {"W": "work", "F": "force", "d": "distance", "theta": "angle"}},
        {"name": "Мощность",
         "equation": Eq(P, W / t),
         "type": "mathematic",
         "category": "physics",
         "variables": {"P": "power", "W": "work", "t": "time"}},

        # Финансы
        {"name": "Формула сложного процента",
         "equation": Eq(A, P * (1 + r / n) ** (n * t)),
         "type": "mathematic",
         "category": "finance",
         "variables": {"A": "amount", "P": "principal", "r": "rate", "n": "compounding_frequency", "t": "time"}},
        {"name": "Формула аннуитета",
         "equation": Eq(PMT, P * r / (1 - (1 + r) ** -n)),
         "type": "mathematic",
         "category": "finance",
         "variables": {"PMT": "payment", "P": "principal", "r": "rate", "n": "number_of_payments"}}

    ]


    for formula in formulas:
        formula_id = add_formula(
            conn,
            name=formula["name"],
            equation=formula["equation"],
            formula_type=formula["type"],
            category=formula.get("category"),
            variables=formula.get("variables"),
            tags=formula.get("tags") # Добавлено tags
        )
        if formula_id:
            print(f"Формула добавлена с ID: {formula_id}")

    conn.close()

if __name__ == "__main__":
    main()
