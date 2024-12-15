const libraryButtons = document.querySelectorAll("#math-library button");
libraryButtons.forEach(button => {
    button.addEventListener("click", () => {
        const latex = button.dataset.latex;
        const textarea = document.getElementById("latex-input");
        textarea.value += latex;
        textarea.focus();
        renderFormula("latex-input"); // Вызываем рендеринг ПОСЛЕ обновления поля
    });
});

const physicsLibraryButtons = document.querySelectorAll("#physics-library button");
physicsLibraryButtons.forEach(button => {
    button.addEventListener("click", () => {
        const latex = button.dataset.latex;
        const textarea = document.getElementById("latex-physics-input");
        textarea.value += latex;
        textarea.focus();
        renderFormula("latex-physics-input"); // Вызываем рендеринг ПОСЛЕ обновления поля
    });
});

// Переключение вкладок
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', function () {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.content-section').forEach(c => c.classList.remove('active'));
        this.classList.add('active');
        const activeSectionId = this.getAttribute('data-tab');
        const activeSection = document.getElementById(activeSectionId);
        document.getElementById("latex-input").value = "";
        document.getElementById("latex-physics-input").value = "";
        activeSection.classList.add('active');
        const output = document.getElementById("formula-output");
        output.innerHTML = "";
    });
});

// Рендеринг формул
function renderFormula(inputId) {
    const input = document.getElementById(inputId).value;
    const sanitizedInput = input.replace(/\\\\/g, '\\');
    const output = document.getElementById("formula-output");
    output.innerHTML = "$$" + sanitizedInput + "$$";
    MathJax.typesetPromise([output]).catch(err => console.error(err));
}

document.getElementById("render-btn").addEventListener("click", () => renderFormula("latex-input"));
document.getElementById("render-physics-btn").addEventListener("click", () => renderFormula("latex-physics-input"));

async function insertAndRender(latex, textareaId) {
    const textarea = document.getElementById(textareaId);
    textarea.value += latex;
    textarea.focus();

    //MathJax.typesetPromise([textarea]).catch(err => console.error(err));
    renderFormula(textareaId); // рендерим формулу чтобы было видно
}


// Преобразование обычной формулы в LaTeX
function convertNormalToLatex(normalText) {
    let latexText = normalText;
    latexText = latexText.replace(/\+/g, "+");
    latexText = latexText.replace(/-/g, "-");
    latexText = latexText.replace(/\*/g, "\\cdot ");
    latexText = latexText.replace(/\//g, "\\div ");
    latexText = latexText.replace(/=/g, "=");
    latexText = latexText.replace(/\^(\d+)/g, "^{$1}");
    latexText = latexText.replace(/\^\((.+?)\)/g, "^{$1}");
    latexText = latexText.replace(/(\w+)\/(\w+)/g, "\\frac{$1}{$2}");
    latexText = latexText.replace(/sqrt\((.+?)\)/g, "\\sqrt{$1}");
    latexText = latexText.replace(/alpha/gi, "\\alpha");
    latexText = latexText.replace(/beta/gi, "\\beta");
    latexText = latexText.replace(/gamma/gi, "\\gamma");
    latexText = latexText.replace(/delta/gi, "\\delta");
    latexText = latexText.replace(/pi/gi, "\\pi");
    latexText = latexText.replace(/theta/gi, "\\theta");
    latexText = latexText.replace(/lambda/gi, "\\lambda");
    latexText = latexText.replace(/varepsilon/gi, "\\varepsilon");
    latexText = latexText.replace(/Gamma/gi, "\\Gamma");

    // Исправление для операций с использованием переменных и знаков
    latexText = latexText.replace(/([A-Za-z]+)([A-Za-z0-9])/g, '$1$2'); // Чтобы переменные в формулах не разделялись
    return latexText;
}

async function saveFormula(type, formula, name) {
    if (!formula || !name) {
        alert("Формула и название не могут быть пустыми!");
        return null;
    }

    try {
        const response = await fetch("/api/save_formula", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                latex: formula,
                formula_type: type, // Передаем тип формулы (math/physics)
                name: name // Передаем название формулы
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Ошибка сохранения: ${response.status} ${errorText}`);
        }

        // Сервер должен возвращать объект с полями id, latex, name
        return await response.json();
    } catch (error) {
        console.error("Ошибка:", error);
        alert(error.message);
        return null;
    }
}



document.getElementById("convert-to-latex-btn").addEventListener("click", function () {
    const normalInput = document.getElementById("normal-input").value.trim();
    if (normalInput === "") {
        alert("Введите обычную формулу для преобразования!");
        return;
    }
    const latexResult = convertNormalToLatex(normalInput);
    const outputBox = document.getElementById("normal-to-latex-output");
    outputBox.textContent = latexResult;
});

const editSection = document.getElementById("edit-section");
const editInput = document.getElementById("edit-input");
const updateBtn = document.getElementById("update-btn");
const cancelBtn = document.getElementById("cancel-btn");
let currentEditItem = null; // Хранит текущий редактируемый элемент

// Обработчик сохранения математической формулы
document.getElementById("save-math-btn").addEventListener("click", async () => {
    const formula = document.getElementById("latex-input").value.trim();
    const name = document.getElementById("formula-name").value.trim(); // Получаем название формулы
    if (!formula || !name) {
        alert("Введите формулу и название перед сохранением!");
        return;
    }
    try {
        const savedFormula = await saveFormula("math", formula, name);
        if (savedFormula) {
            addFormulaToList("math", savedFormula);
            document.getElementById("formula-name").value = ""; // Очищаем поле ввода названия
        }
    } catch (error) {
        alert("Не удалось сохранить формулу: " + error.message);
    }
});

// Аналогично для физической формулы
document.getElementById("save-physics-btn").addEventListener("click", async () => {
    const formula = document.getElementById("latex-physics-input").value.trim(); // Получаем формулу
    const name = document.getElementById("formula-name").value.trim(); // Получаем название
    if (!formula || !name) {
        alert("Введите физическую формулу и название перед сохранением!");
        return;
    }
    try {
        // Вызываем функцию сохранения с типом "physics"
        const savedFormula = await saveFormula("physics", formula, name);
        if (savedFormula) {
            addFormulaToList("physics", savedFormula); // Добавляем в список физ. формул
            document.getElementById("formula-name").value = ""; // Очищаем поле ввода названия
        }
    } catch (error) {
        alert("Не удалось сохранить физическую формулу: " + error.message);
    }
});


// Обновляем функцию сохранения формулы
async function saveFormula(type, formula, name) {
    if (!formula || !name) {
        alert("Формула и название не могут быть пустыми!");
        return null;
    }

    try {
        const response = await fetch("/api/save_formula", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                latex: formula,
                formula_type: type,
                name: name
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Ошибка сохранения: ${response.status} ${errorText}`);
        }

        // Сервер должен возвращать объект с полями id, latex, name
        return await response.json();
    } catch (error) {
        console.error("Ошибка:", error);
        alert(error.message);
        return null;
    }
}

// Обновляем отображение сохраненной формулы
function addFormulaToList(type, formula) {
    const list = document.getElementById(`saved-${type}-list`);
    const listItem = document.createElement("li");
    listItem.dataset.id = formula.id; // Храним ID формулы из базы данных

    // Проверяем, есть ли название формулы
    const formulaName = formula.name ? formula.name : "Без названия";

    listItem.innerHTML = `
        <span class="formula-name">${formulaName}:</span>
        <span class="formula-text">${formula.latex}</span>
        <button class="edit-btn">Редактировать</button>
        <button class="delete-btn">Удалить</button>
    `;
    list.appendChild(listItem);

    // Добавляем обработчики для редактирования и удаления
    listItem.querySelector(".edit-btn").addEventListener("click", () => startEditing(listItem));
    listItem.querySelector(".delete-btn").addEventListener("click", () => deleteFormula(listItem, type));
}


// Удаление формулы
async function deleteFormula(listItem, type) {
    const formulaId = listItem.dataset.id;
    if (!formulaId) {
        alert("Не удалось найти ID формулы для удаления.");
        return;
    }

    try {
        const response = await fetch(`/api/delete_formula/${formulaId}`, {
            method: 'DELETE',
        });

        if (!response.ok) throw new Error('Ошибка при удалении формулы.');

        // Удаляем элемент из списка после успешного удаления на сервере
        listItem.remove();
    } catch (error) {
        alert("Ошибка при удалении формулы: " + error.message);
    }
}

// Редактирование формулы с учетом сохранения в базу данных
updateBtn.addEventListener("click", async () => {
    if (currentEditItem) {
        const updatedFormula = editInput.value.trim();
        const formulaId = currentEditItem.dataset.id;

        if (updatedFormula && formulaId) {
            try {
                const response = await fetch(`/api/update_formula/${formulaId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ latex: updatedFormula }),
                });

                if (!response.ok) throw new Error('Ошибка обновления формулы.');

                currentEditItem.querySelector(".formula-text").textContent = updatedFormula;
                editSection.classList.add("hidden");
                currentEditItem = null;
            } catch (error) {
                alert("Ошибка при обновлении формулы: " + error.message);
            }
        }
    }
});


function startEditing(listItem) {
    const formulaText = listItem.querySelector(".formula-text").textContent;
    editInput.value = formulaText;
    currentEditItem = listItem;
    editSection.classList.remove("hidden");
}



cancelBtn.addEventListener("click", () => {
    editSection.classList.add("hidden");
    currentEditItem = null;
});
