const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const fileInfo = document.getElementById("fileInfo");
const fileName = document.getElementById("fileName");
const sheetSelector = document.getElementById("sheetSelector");
const sheetTabs = document.getElementById("sheetTabs");
const sheetPanel = document.getElementById("sheetPanel");
const selectionSummary = document.getElementById("selectionSummary");
const chunkOptions = document.getElementById("chunkOptions");
const enableChunking = document.getElementById("enableChunking");
const chunkSizeControl = document.getElementById("chunkSizeControl");
const chunkSize = document.getElementById("chunkSize");
const customChunkSize = document.getElementById("customChunkSize");
const convertBtn = document.getElementById("convertBtn");
const loading = document.getElementById("loading");
const loadingText = document.getElementById("loadingText");
const progressLabel = document.getElementById("progressLabel");
const progressPercent = document.getElementById("progressPercent");
const progressFill = document.getElementById("progressFill");
const errorMessage = document.getElementById("errorMessage");
const resultSection = document.getElementById("resultSection");
const chunkInfo = document.getElementById("chunkInfo");
const chunkNote = document.getElementById("chunkNote");
const totalChunks = document.getElementById("totalChunks");
const displayChunkSize = document.getElementById("displayChunkSize");
const chunksContainer = document.getElementById("chunksContainer");
const copyAllBtn = document.getElementById("copyAllBtn");
const downloadBtn = document.getElementById("downloadBtn");
const clearBtn = document.getElementById("clearBtn");
const selectAllBtn = document.getElementById("selectAllBtn");
const clearSelectionBtn = document.getElementById("clearSelectionBtn");
const successMessage = document.getElementById("successMessage");

let selectedFile = null;
let workbookSheets = [];
let selectedColumnsBySheet = {};
let activeSheetName = null;
let currentChunks = [];
let progressTimers = [];

dropZone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (event) => handleFile(event.target.files[0]));
dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropZone.classList.add("dragover");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragover");
    handleFile(event.dataTransfer.files[0]);
});

enableChunking.addEventListener("change", () => {
    chunkSizeControl.style.display = enableChunking.checked ? "block" : "none";
});

chunkSize.addEventListener("change", () => {
    customChunkSize.style.display = chunkSize.value === "custom" ? "inline-block" : "none";
});

selectAllBtn.addEventListener("click", () => applySelection("all"));
clearSelectionBtn.addEventListener("click", () => applySelection("none"));

convertBtn.addEventListener("click", async () => {
    if (!selectedFile) {
        return;
    }

    const selection = buildSelectionPayload();
    const selectedCount = Object.values(selection).reduce((sum, columns) => sum + columns.length, 0);
    if (!selectedCount) {
        showError("Select at least one column before converting.");
        return;
    }

    setLoadingState(true, "Converting your workbook...", "Uploading file...", 8);
    startProgressSimulation([
        { percent: 22, delay: 180, label: "Uploading file..." },
        { percent: 46, delay: 320, label: "Applying sheet and column selection..." },
        { percent: 72, delay: 420, label: "Building Markdown..." },
        { percent: 90, delay: 520, label: "Splitting into AI-ready chunks..." }
    ]);
    hideError();
    hideSuccess();
    resultSection.classList.remove("show");
    chunksContainer.innerHTML = "";
    currentChunks = [];

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("selection", JSON.stringify(selection));

    let url = "/convert";
    const requestedChunkSize = getChunkSize();
    if (requestedChunkSize) {
        url = `/convert?chunk_size=${requestedChunkSize}`;
    }

    try {
        const response = await fetch(url, { method: "POST", body: formData });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Conversion failed");
        }

        setProgressState(100, "Completed");

        if (data.chunked && Array.isArray(data.chunks)) {
            displayChunkedResult(data);
        } else {
            displaySingleResult(data.markdown);
        }

        const chunkCount = data.chunks ? data.chunks.length : 1;
        showSuccess(`File converted successfully. Ready to paste as ${chunkCount} message chunk(s).`);
        resultSection.scrollIntoView({ behavior: "smooth" });
    } catch (error) {
        showError(error.message || "Conversion failed.");
    } finally {
        setLoadingState(false);
    }
});

copyAllBtn.addEventListener("click", () => {
    if (!currentChunks.length) {
        return;
    }
    const text = currentChunks.map((chunk, index) =>
        `<!-- Chunk ${index + 1}/${currentChunks.length} -->\n\n${chunk}`
    ).join("\n\n---\n\n");
    navigator.clipboard.writeText(text).then(() => {
        showSuccess("All chunks copied to clipboard.");
        setTimeout(hideSuccess, 2000);
    });
});

downloadBtn.addEventListener("click", () => {
    if (!currentChunks.length || !selectedFile) {
        return;
    }
    const text = currentChunks.map((chunk, index) =>
        `<!-- Chunk ${index + 1}/${currentChunks.length} -->\n\n${chunk}`
    ).join("\n\n---\n\n");
    const blob = new Blob([text], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = selectedFile.name.replace(/\.(xlsx|xls)$/i, ".md");
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
    showSuccess("Markdown file downloaded.");
    setTimeout(hideSuccess, 2000);
});

clearBtn.addEventListener("click", resetApp);

async function handleFile(file) {
    if (!file) {
        return;
    }
    const validExtension = file.name.endsWith(".xlsx") || file.name.endsWith(".xls");
    if (!validExtension) {
        showError("Please upload a valid Excel file (.xlsx or .xls).");
        return;
    }

    resetStateForNewFile(file);
    setLoadingState(true, "Inspecting your workbook...", "Uploading workbook...", 8);
    startProgressSimulation([
        { percent: 24, delay: 180, label: "Uploading workbook..." },
        { percent: 58, delay: 320, label: "Reading sheets..." },
        { percent: 84, delay: 420, label: "Collecting columns..." }
    ]);

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/inspect", { method: "POST", body: formData });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Failed to inspect workbook.");
        }

        setProgressState(100, "Completed");

        workbookSheets = Array.isArray(data.sheets) ? data.sheets : [];
        if (!workbookSheets.length) {
            throw new Error("No sheets were found in this workbook.");
        }

        selectedColumnsBySheet = {};
        workbookSheets.forEach((sheet) => {
            selectedColumnsBySheet[sheet.name] = [...sheet.columns];
        });
        activeSheetName = workbookSheets[0].name;

        sheetSelector.classList.add("show");
        chunkOptions.style.display = "block";
        chunkSizeControl.style.display = enableChunking.checked ? "block" : "none";
        convertBtn.disabled = false;
        renderSheetTabs();
        renderActiveSheet();
        updateSelectionSummary();
    } catch (error) {
        resetApp();
        showError(error.message || "Failed to inspect workbook.");
    } finally {
        setLoadingState(false);
    }
}

function applySelection(mode) {
    workbookSheets.forEach((sheet) => {
        selectedColumnsBySheet[sheet.name] = mode === "all" ? [...sheet.columns] : [];
    });
    renderSheetTabs();
    renderActiveSheet();
    updateSelectionSummary();
}

function resetStateForNewFile(file) {
    selectedFile = file;
    workbookSheets = [];
    selectedColumnsBySheet = {};
    activeSheetName = null;
    currentChunks = [];
    fileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
    fileInfo.classList.add("show");
    sheetTabs.innerHTML = "";
    sheetPanel.innerHTML = "";
    sheetSelector.classList.remove("show");
    resultSection.classList.remove("show");
    chunksContainer.innerHTML = "";
    convertBtn.disabled = true;
    setProgressState(0, "Preparing...");
    hideError();
    hideSuccess();
}

function resetApp() {
    selectedFile = null;
    workbookSheets = [];
    selectedColumnsBySheet = {};
    activeSheetName = null;
    currentChunks = [];
    fileInput.value = "";
    fileInfo.classList.remove("show");
    sheetSelector.classList.remove("show");
    chunkOptions.style.display = "none";
    chunkInfo.style.display = "none";
    chunkNote.style.display = "none";
    resultSection.classList.remove("show");
    chunksContainer.innerHTML = "";
    convertBtn.disabled = true;
    setProgressState(0, "Preparing...");
    hideError();
    hideSuccess();
}

function renderSheetTabs() {
    sheetTabs.innerHTML = "";
    workbookSheets.forEach((sheet) => {
        const selectedCount = (selectedColumnsBySheet[sheet.name] || []).length;
        const button = document.createElement("button");
        button.type = "button";
        button.className = `sheet-tab${sheet.name === activeSheetName ? " active" : ""}`;
        button.innerHTML = `<span>${escapeHtml(sheet.name)}</span><span class="sheet-tab-badge">${selectedCount}</span>`;
        button.addEventListener("click", () => {
            activeSheetName = sheet.name;
            renderSheetTabs();
            renderActiveSheet();
        });
        sheetTabs.appendChild(button);
    });
}

function renderActiveSheet() {
    const sheet = workbookSheets.find((entry) => entry.name === activeSheetName);
    if (!sheet) {
        sheetPanel.innerHTML = "";
        return;
    }

    const selectedColumns = new Set(selectedColumnsBySheet[sheet.name] || []);
    const columnsHtml = sheet.columns.map((column) => `
        <label class="column-option">
            <input type="checkbox" data-sheet="${escapeAttribute(sheet.name)}" data-column="${escapeAttribute(column)}" ${selectedColumns.has(column) ? "checked" : ""}>
            <span>${escapeHtml(column)}</span>
        </label>
    `).join("");

    sheetPanel.innerHTML = `
        <div class="sheet-panel-header">
            <div>
                <h3>${escapeHtml(sheet.name)}</h3>
                <p class="sheet-meta">${sheet.total_rows} row(s) - ${sheet.total_columns} column(s)</p>
            </div>
            <div class="action-buttons">
                <button class="btn btn-copy btn-small" id="selectSheetColumnsBtn" type="button">Select Sheet</button>
                <button class="btn btn-clear btn-small" id="clearSheetColumnsBtn" type="button">Clear Sheet</button>
            </div>
        </div>
        <p class="selector-summary">Only selected columns from selected sheets will be included in the Markdown output and chunking flow.</p>
        <div class="column-grid">${columnsHtml || "<p>No columns found.</p>"}</div>
    `;

    document.getElementById("selectSheetColumnsBtn").addEventListener("click", () => {
        selectedColumnsBySheet[sheet.name] = [...sheet.columns];
        renderSheetTabs();
        renderActiveSheet();
        updateSelectionSummary();
    });

    document.getElementById("clearSheetColumnsBtn").addEventListener("click", () => {
        selectedColumnsBySheet[sheet.name] = [];
        renderSheetTabs();
        renderActiveSheet();
        updateSelectionSummary();
    });

    sheetPanel.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
            const sheetName = checkbox.dataset.sheet;
            const columnName = checkbox.dataset.column;
            const nextSelection = new Set(selectedColumnsBySheet[sheetName] || []);
            if (checkbox.checked) {
                nextSelection.add(columnName);
            } else {
                nextSelection.delete(columnName);
            }
            const sheetDefinition = workbookSheets.find((entry) => entry.name === sheetName);
            selectedColumnsBySheet[sheetName] = sheetDefinition.columns.filter((column) => nextSelection.has(column));
            renderSheetTabs();
            updateSelectionSummary();
        });
    });
}

function updateSelectionSummary() {
    const selectedSheets = workbookSheets.filter((sheet) => (selectedColumnsBySheet[sheet.name] || []).length > 0).length;
    const selectedColumns = workbookSheets.reduce((total, sheet) => total + (selectedColumnsBySheet[sheet.name] || []).length, 0);
    selectionSummary.textContent = `${selectedSheets} sheet(s) active - ${selectedColumns} column(s) selected for Markdown chunking`;
}

function buildSelectionPayload() {
    const payload = {};
    workbookSheets.forEach((sheet) => {
        const columns = selectedColumnsBySheet[sheet.name] || [];
        if (columns.length > 0) {
            payload[sheet.name] = columns;
        }
    });
    return payload;
}

function getChunkSize() {
    if (!enableChunking.checked) {
        return null;
    }
    if (chunkSize.value === "custom") {
        const value = parseInt(customChunkSize.value, 10);
        return Number.isFinite(value) && value > 0 ? value : null;
    }
    return parseInt(chunkSize.value, 10);
}

function displaySingleResult(markdown) {
    currentChunks = [markdown];
    resultSection.classList.add("show");
    chunkInfo.style.display = "none";
    chunkNote.style.display = "block";
    chunksContainer.innerHTML = `
        <div class="chunk-container">
            <div class="chunk-header">
                <h3>📄 Full Output</h3>
                <span class="chunk-size">${markdown.length} chars</span>
                <div class="chunk-actions">
                    <button class="btn btn-small" onclick="copyChunk(0)">📋 Copy</button>
                </div>
            </div>
            <div class="markdown-output">${escapeHtml(markdown)}</div>
        </div>
    `;
}

function displayChunkedResult(data) {
    currentChunks = data.chunks;
    resultSection.classList.add("show");
    chunkInfo.style.display = data.total_chunks > 1 ? "block" : "none";
    chunkNote.style.display = data.total_chunks <= 1 ? "block" : "none";
    totalChunks.textContent = data.total_chunks;
    displayChunkSize.textContent = data.chunk_size;
    chunksContainer.innerHTML = "";

    data.chunks.forEach((chunk, index) => {
        const chunkDiv = document.createElement("div");
        chunkDiv.className = "chunk-container";
        chunkDiv.innerHTML = `
            <div class="chunk-header">
                <h3>📦 Chunk ${index + 1} of ${data.total_chunks}</h3>
                <span class="chunk-size">${chunk.length} chars</span>
                <div class="chunk-actions">
                    <button class="btn btn-small" onclick="copyChunk(${index})">📋 Copy</button>
                </div>
            </div>
            <div class="markdown-output">${escapeHtml(chunk)}</div>
        `;
        chunksContainer.appendChild(chunkDiv);
    });
}

function setLoadingState(isLoading, message = "") {
    loading.classList.toggle("show", isLoading);
    if (message) {
        loadingText.textContent = message;
    }
    if (!isLoading) {
        clearProgressSimulation();
    }
}

function setProgressState(percent, label = "") {
    const safePercent = Math.max(0, Math.min(100, Math.round(percent)));
    progressFill.style.width = `${safePercent}%`;
    progressPercent.textContent = `${safePercent}%`;
    if (label) {
        progressLabel.textContent = label;
    }
}

function startProgressSimulation(steps) {
    clearProgressSimulation();
    let elapsed = 0;
    steps.forEach((step) => {
        elapsed += step.delay;
        const timer = setTimeout(() => {
            setProgressState(step.percent, step.label);
        }, elapsed);
        progressTimers.push(timer);
    });
}

function clearProgressSimulation() {
    progressTimers.forEach((timer) => clearTimeout(timer));
    progressTimers = [];
}

function formatFileSize(bytes) {
    if (bytes < 1024) {
        return `${bytes} B`;
    }
    if (bytes < 1048576) {
        return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / 1048576).toFixed(1)} MB`;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttribute(text) {
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/"/g, "&quot;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add("show");
}

function hideError() {
    errorMessage.classList.remove("show");
}

function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.classList.add("show");
}

function hideSuccess() {
    successMessage.classList.remove("show");
}

window.copyChunk = function copyChunk(index) {
    if (!currentChunks[index]) {
        return;
    }
    navigator.clipboard.writeText(currentChunks[index]).then(() => {
        showSuccess(`Chunk ${index + 1} copied to clipboard.`);
        setTimeout(hideSuccess, 2000);
    });
};
