import re
from flask import Flask, render_template, request, jsonify
from difflib import SequenceMatcher
import psycopg2
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import hashlib
import json
import Levenshtein

# Загрузка модели
model = SentenceTransformer('C:/Users/danil/hackoton/all-MiniLM-L6-v2')

app = Flask(__name__)

# Настройки подключения к PostgreSQL
DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'admin',
    'host': '127.0.0.1',
    'port': 5432
}


# Функция для подключения к базе данных
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def enhance_formula_with_context(formula, context=None):
    """Добавление контекста (например, переменных или категорий) к формуле."""
    if context:
        return f"{formula} | Context: {context}"
    return formula

def calculate_combined_similarity(input_formula, saved_formulas, threshold=0.7):
    input_formula = normalize_formula(input_formula)
    saved_formulas = [normalize_formula(formula['latex']) for formula in saved_formulas]

    # Шаг 1: Нейросетевое сходство
    neural_similarities = calculate_neural_similarity(input_formula, [f['latex'] for f in saved_formulas])

    # Шаг 2: Сравнение с помощью метрик строк (Levenshtein, Jaccard)
    string_similarities = [
        {
            'latex': formula['latex'],
            'name': formula['name'],
            'levenshtein': calculate_levenshtein_similarity(input_formula, formula['latex']),
            'jaccard': calculate_jaccard_similarity(input_formula, formula['latex'])
        }
        for formula in saved_formulas
    ]

    # Шаг 3: Объединение сходства (взвешиваем нейросетевое и строковое сходство)
    combined_results = []
    for formula, neural_sim, string_sim in zip(saved_formulas, neural_similarities, string_similarities):
        # Применяем веса для разных методов сравнения
        combined_similarity = (neural_sim * 0.4) + (string_sim['levenshtein'] * 0.3) + (string_sim['jaccard'] * 0.3)

        # Выбираем лучший метод
        best_method = 'neural_network' if neural_sim > max(string_sim['levenshtein'], string_sim['jaccard']) else 'string_methods'

        combined_results.append({
            'formula': formula['latex'],
            'name': formula['name'],
            'neural_similarity': neural_sim,
            'levenshtein_similarity': string_sim['levenshtein'],
            'jaccard_similarity': string_sim['jaccard'],
            'combined_similarity': combined_similarity,
            'best_method': best_method
        })

    # Сортируем результаты по комбинированному сходству
    return sorted(combined_results, key=lambda x: x['combined_similarity'], reverse=True)


def preprocess_formula(formula):
    """Обработать формулу для улучшения результатов сравнения."""
    # Убираем пробелы, нормализуем степени и т.д.
    formula = re.sub(r'\s+', '', formula)
    formula = re.sub(r'\^\{(.*?)\}', r'^\1', formula)
    return formula


def calculate_neural_similarity(input_formula, db_formulas, threshold=0.7):
    """Сравнение формул через нейросеть с порогом для точности."""
    input_formula = preprocess_formula(input_formula)
    db_formulas = [preprocess_formula(formula) for formula in db_formulas]
    input_vector = model.encode(input_formula)  # Закодированная формула
    db_vectors = [model.encode(formula) for formula in db_formulas]
    similarities = cosine_similarity([input_vector], db_vectors)[0]

    # Применение порогового значения для фильтрации
    return [float(sim) if sim > threshold else 0 for sim in similarities]


# Рассчитываем схожесть строк
def calculate_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def calculate_levenshtein_similarity(a, b):
    return Levenshtein.ratio(a, b)

def calculate_jaccard_similarity(a, b):
    a_set = set(a)
    b_set = set(b)
    intersection = len(a_set.intersection(b_set))
    union = len(a_set.union(b_set))
    return intersection / union

def normalize_formula(formula):
    # Преобразование степеней, дробей и других элементов в единую форму
    formula = formula.replace("a^b", "a^{b}")  # Пример преобразования
    formula = formula.replace("frac{a}{b}", "\\frac{a}{b}")
    formula = formula.replace("log(a)", "log{(a)}")
    formula = formula.replace("log(ab)", "log{(ab)}")

    # Убираем все пробелы для более строгого сравнения
    formula = re.sub(r'\s+', '', formula)

    # Нормализуем степени (для LaTeX-формул)
    formula = re.sub(r'\^\{(.*?)\}', r'^\1', formula)  # Убираем лишние скобки у степеней

    # Преобразуем дроби в общий формат
    formula = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'\\frac{\1}{\2}', formula)

    # Нормализуем выражения логарифмов и корней
    formula = re.sub(r'\\sqrt\{([^{}]+)\}', r'\\sqrt{\1}', formula)

    return formula


def normalize_formula1(formula):
    # Преобразуем все степени в формат a^{b}, если они записаны как a^b
    formula = re.sub(r'([a-zA-Z0-9])\^([a-zA-Z0-9])', r'\1^{\2}', formula)

    # Преобразуем все дроби в формат \frac{a}{b}, если они записаны как frac{a}{b}
    formula = re.sub(r'frac{([a-zA-Z0-9]+)}{([a-zA-Z0-9]+)}', r'\\frac{\1}{\2}', formula)

    return formula


# Генерация хэша формулы
def generate_formula_hash(formula):
    """Генерирует хэш для нормализованной формулы."""
    normalized = normalize_formula1(formula)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


@app.route('/')
def editor():
    return render_template('editor.html')
@app.route('/compare')
def compare():
    return render_template('compare.html')


@app.route('/editor')
def editor1():
    return render_template('editor.html')


@app.route('/compare_formula', methods=['POST'])
def compare_formula():
    data = request.get_json()
    input_formula = data.get('formula', '').strip()
    print("Полученные данные:", data)

    if not input_formula:
        return jsonify({'error': 'Формула пуста!'}), 400

    normalized_input = normalize_formula(input_formula)
    print("Нормализованная входная формула:", normalized_input)

    try:
        # Подключение к базе данных
        conn = get_db_connection()
        cursor = conn.cursor()

        # Извлекаем сохраненные формулы с именами
        cursor.execute("SELECT latex, name FROM formulas")
        saved_formulas = [{'latex': row[0], 'name': row[1]} for row in cursor.fetchall()]
        print("Сохраненные формулы из базы данных:", saved_formulas)

        # Сравнение с базой данных по Левенштейну и Жаккарду
        string_similarities = [
            {
                'latex': formula['latex'],
                'name': formula['name'],
                'levenshtein': calculate_levenshtein_similarity(normalized_input, formula['latex']),
                'jaccard': calculate_jaccard_similarity(normalized_input, formula['latex'])
            }
            for formula in saved_formulas
        ]
        print("Сходства по строкам:", string_similarities)

        # Сравнение через нейросеть
        neural_similarities = calculate_neural_similarity(normalized_input, [f['latex'] for f in saved_formulas])
        print("Сходства по нейросети:", neural_similarities)

        # Объединяем результаты
        combined_results = []
        for formula, neural_sim, string_sim in zip(saved_formulas, neural_similarities, string_similarities):
            # Проверка, что string_sim является словарем
            if isinstance(string_sim, dict):
                combined_similarity = (neural_sim * 0.4) + (string_sim['levenshtein'] * 0.3) + (string_sim['jaccard'] * 0.3)
            else:
                app.logger.error(f"Ошибка: string_sim должен быть словарем, но получен {type(string_sim)}")
                combined_similarity = 0  # Если ошибка, ставим сходство в 0

            similarity_scores = {
                'neural_network': neural_sim,
                'levenshtein': string_sim.get('levenshtein', 0),
                'jaccard': string_sim.get('jaccard', 0),
                'combined': combined_similarity
            }

            best_method = max(similarity_scores, key=similarity_scores.get)

            combined_results.append({
                'formula': formula['latex'],
                'name': formula['name'],
                'neural_similarity': neural_sim,
                'levenshtein': string_sim.get('levenshtein', 0),
                'jaccard': string_sim.get('jaccard', 0),
                'combined_similarity': combined_similarity,
                'best_method': best_method,
                'similarity_scores': similarity_scores
            })

        # Сортируем по наибольшему сходству
        return jsonify({
            'matches': sorted(combined_results, key=lambda x: x['similarity_scores'][x['best_method']], reverse=True)[:5]
        })

    except Exception as e:
        app.logger.error(f"Ошибка при работе с формулами: {str(e)}")
        return jsonify({"error": "Ошибка при сравнении формулы"}), 500

    finally:
        cursor.close()
        conn.close()


@app.route('/api/save_formula', methods=['POST'])
def save_formula():
    data = request.get_json()
    print("Полученные данные:", data)  # Отладка: вывод данных из запроса

    # Проверяем, чтобы все обязательные поля были переданы
    if not data or 'latex' not in data or 'formula_type' not in data or 'name' not in data:
        return jsonify({'error': 'Некорректные данные! Убедитесь, что указаны latex, formula_type и name.'}), 400

    # Нормализуем LaTeX строку
    normalized_latex = normalize_formula1(data['latex'].strip())
    print("Нормализованная формула:", normalized_latex)

    # Преобразуем структуру, переменные и теги в JSON
    try:
        structure = json.dumps(data.get('structure', {}))  # Делаем структуру пустым словарем, если она не передана
        variables = json.dumps(data.get('variables', {}))
        tags = json.dumps(data.get('tags', []))
    except Exception as e:
        return jsonify({'error': 'Ошибка обработки данных!'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Проверяем, существует ли формула с таким же названием
        cursor.execute("SELECT id FROM formulas WHERE LOWER(name) = LOWER(%s)", (data['name'],))
        existing_formula = cursor.fetchone()

        if existing_formula:
            app.logger.info(f"Формула с таким названием уже существует: ID {existing_formula[0]}")
            return jsonify({'error': 'Формула с таким названием уже существует в базе данных!', 'id': existing_formula[0]}), 400

        # Проверяем, существует ли формула с таким же LaTeX содержанием
        cursor.execute("SELECT id FROM formulas WHERE LOWER(latex) = LOWER(%s)", (normalized_latex,))
        existing_latex_formula = cursor.fetchone()

        if existing_latex_formula:
            app.logger.info(f"Формула с таким содержанием уже существует: ID {existing_latex_formula[0]}")
            return jsonify({'error': 'Формула с таким содержанием уже существует в базе данных!', 'id': existing_latex_formula[0]}), 400

        # Вставка новой формулы
        cursor.execute(""" 
            INSERT INTO formulas (name, latex, structure, formula_type, category, variables, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['name'],  # Имя формулы
            normalized_latex,  # Нормализованное LaTeX представление
            structure,  # JSON структура
            data['formula_type'],  # Тип формулы
            data.get('category'),  # Категория
            variables,  # Связанные переменные
            tags  # Теги
        ))

        formula_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({'id': formula_id, 'latex': normalized_latex, 'name': data['name']}), 201

    except Exception as e:
        print(f"Ошибка сохранения формулы: {e}")
        return jsonify({'error': 'Не удалось сохранить формулу!'}), 500

    finally:
        cursor.close()
        conn.close()



# API для редактирования формулы
@app.route('/api/update_formula/<int:formula_id>', methods=['PUT'])
def edit_formula(formula_id):
    data = request.get_json()
    if not data or 'latex' not in data:
        return jsonify({'error': 'Некорректные данные'}), 400

    new_latex = data['latex']
    new_structure = data.get('structure', {})
    new_category = data.get('category', '')
    new_variables = data.get('variables', {})
    new_tags = data.get('tags', [])

    # Подключение к базе данных
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Обновление формулы в базе данных
        cursor.execute("""
            UPDATE formulas
            SET latex = %s, structure = %s, category = %s, variables = %s, tags = %s, formula_hash = %s
            WHERE id = %s
            RETURNING id;
        """, (new_latex, json.dumps(new_structure), new_category, json.dumps(new_variables),
              json.dumps(new_tags), generate_formula_hash(new_latex), formula_id))

        conn.commit()
        return jsonify({'id': formula_id, 'latex': new_latex}), 200

    except Exception as e:
        return jsonify({'error': 'Ошибка при редактировании формулы'}), 500

    finally:
        cursor.close()
        conn.close()

# API для удаления формулы
@app.route('/api/delete_formula/<int:formula_id>', methods=['DELETE'])
def delete_formula(formula_id):
    # Подключение к базе данных
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Удаление формулы из базы данных
        cursor.execute("DELETE FROM formulas WHERE id = %s", (formula_id,))
        conn.commit()

        return '', 204

    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Ошибка при удалении формулы'}), 500

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)
