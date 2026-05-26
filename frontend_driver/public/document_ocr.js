// ───────────────────────────────────────────────────────────────────────────
// Document OCR (backend engines: EasyOCR / RapidOCR).
//
// EasyOCR and RapidOCR are Python image-OCR engines, so recognition runs on the
// backend (/api/ocr/{engine}). Results flow through window.DocumentReader.analyze().
//
//   const r = await window.DocumentOCR.read(file, { engine, onProgress });
//   // r = { fields, lines, table, text, pages }
//
(function () {
    const BASE = "http://127.0.0.1:9000/api/ocr/";

    function readAsDataURL(file) {
        return new Promise((resolve, reject) => {
            const r = new FileReader();
            r.onload = () => resolve(r.result);
            r.onerror = reject;
            r.readAsDataURL(file);
        });
    }

    async function ocrImage(dataUrl, engine, label) {
        let res, json;
        try {
            res = await fetch(BASE + engine, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ dataUrl }),
            });
            json = await res.json();
        } catch (err) {
            throw new Error("Could not reach " + label + " backend: " + (err && err.message ? err.message : err));
        }
        if (!res.ok || !json.ok) {
            throw new Error(json && json.error ? json.error : ("HTTP " + res.status));
        }
        return json.words || [];
    }

    async function pdfToPages(file, onProgress) {
        if (!window.pdfjsLib) throw new Error("PDF support (pdf.js) not loaded.");
        if (window.pdfjsLib.GlobalWorkerOptions && !window.pdfjsLib.GlobalWorkerOptions.workerSrc) {
            window.pdfjsLib.GlobalWorkerOptions.workerSrc =
                "https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.worker.min.js";
        }
        const buf = await file.arrayBuffer();
        const pdf = await window.pdfjsLib.getDocument({ data: buf }).promise;
        const pages = [];
        for (let i = 1; i <= pdf.numPages; i++) {
            onProgress(null, `Rendering page ${i}/${pdf.numPages}…`);
            const page = await pdf.getPage(i);
            const viewport = page.getViewport({ scale: 2 });
            const canvas = document.createElement("canvas");
            canvas.width = viewport.width; canvas.height = viewport.height;
            await page.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;
            pages.push({ dataUrl: canvas.toDataURL("image/png"), height: canvas.height });
        }
        return pages;
    }

    async function read(file, opts) {
        opts = opts || {};
        const onProgress = opts.onProgress || function () {};
        const engine = opts.engine === "rapidocr" ? "rapidocr" : "easyocr";
        const label = engine === "rapidocr" ? "RapidOCR" : "EasyOCR";

        if (!window.DocumentReader || !window.DocumentReader.analyze) {
            throw new Error("Shared analyzer not loaded (document.js).");
        }

        const isPdf = file.type === "application/pdf" || /\.pdf$/i.test(file.name);
        let words = [];
        let pageCount = 1;

        if (isPdf) {
            const pages = await pdfToPages(file, onProgress);
            pageCount = pages.length;
            let yOffset = 0;
            for (let i = 0; i < pages.length; i++) {
                onProgress(0.3 + 0.6 * (i / pages.length),
                    `Running ${label} on page ${i + 1}/${pages.length}… (first run loads models)`);
                const pw = await ocrImage(pages[i].dataUrl, engine, label);
                pw.forEach((w) => words.push({
                    text: w.text,
                    x0: w.x0, x1: w.x1,
                    y0: w.y0 + yOffset, y1: w.y1 + yOffset,
                    conf: w.conf,
                }));
                yOffset += pages[i].height + 40;
            }
        } else {
            onProgress(null, "Uploading to " + label + "…");
            const dataUrl = await readAsDataURL(file);
            onProgress(0.3, "Running " + label + " on the server… (first run loads models — please wait)");
            words = await ocrImage(dataUrl, engine, label);
        }

        onProgress(0.9, "Structuring results…");
        const data = {
            text: words.map((w) => w.text).join("\n"),
            lines: words.map((w) => ({
                words: [{ text: w.text, bbox: { x0: w.x0, y0: w.y0, x1: w.x1, y1: w.y1 } }],
            })),
        };
        const out = window.DocumentReader.analyze(data);
        out.pages = pageCount;
        onProgress(1, "Done");
        return out;
    }

    window.DocumentOCR = { read };
})();
