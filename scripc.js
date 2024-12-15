
// Сравнение формул
const formulaInput = document.getElementById("formula-input");
const matchesList = document.getElementById("matches").querySelector("ul");

const cleanFormula = (formula) => {
    return formula.replace(/\s+/g, '').replace(/[{}[\]]/g, '');
};

const highlightDifferences = (input, match) => {
    const cleanedInput = cleanFormula(input);
    const cleanedMatch = cleanFormula(match);

    let highlightedInput = '';
    let highlightedMatch = '';
    const maxLength = Math.max(cleanedInput.length, cleanedMatch.length);

    let allMatched = true; // флаг для отслеживания полного совпадения

    for (let i = 0; i < maxLength; i++) {
        const inputChar = cleanedInput[i] || '';
        const matchChar = cleanedMatch[i] || '';

        if (inputChar === matchChar) {
            highlightedInput += `<span class="match">${inputChar || ' '}</span>`;
            highlightedMatch += `<span class="match">${matchChar || ' '}</span>`;
        } else {
            highlightedInput += `<span class="mismatch">${inputChar || ''}</span>`;
            highlightedMatch += `<span class="mismatch">${matchChar || ''}</span>`;
            allMatched = false;
        }
    }

    return { highlightedInput, highlightedMatch, allMatched };
};

formulaInput.addEventListener("input", async () => {
    const formula = formulaInput.value.trim();

    if (!formula) {
        matchesList.innerHTML = "<li>Введите формулу, чтобы начать сравнение...</li>";
        return;
    }

    try {
        const response = await fetch('/compare_formula', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ formula })
        });

        if (!response.ok) {
            matchesList.innerHTML = "<li>Ошибка при получении данных!</li>";
            return;
        }

        const data = await response.json();

        matchesList.innerHTML = data.matches
            .map(match => {
                const { highlightedInput, highlightedMatch, allMatched } = highlightDifferences(formula, match.formula);

                // Если все символы совпали, устанавливаем сходство на 100%
                const similarity = allMatched ? 100 : (match.combined_similarity * 100).toFixed(2);

                return `
                    <li>
                        <div><strong>Название:</strong> ${match.name || "Без названия"}</div>
                        <div><strong>Введённая формула:</strong> <span class="mathjax">${highlightedInput}</span></div>
                        <div><strong>Формула из базы:</strong> <span class="mathjax">${highlightedMatch}</span></div>
                        <div><strong>Сходство:</strong> <span class="similarity">${similarity}%</span></div>
                    </li>`;
            })
            .join('');
        MathJax.typeset();
    } catch (error) {
        matchesList.innerHTML = "<li>Ошибка соединения с сервером!</li>";
    }
});

