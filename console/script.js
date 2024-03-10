
//const output = document.getElementById("outputResult");
const code = document.getElementById("inputCode");

async function evaluatePython() {
	let pyodide = await pyodideReadyPromise;

	if (code.value == ""){
		addOutputBox("<empty>", "You didn't enter any code! please do.", true); // Display error in red
		return
	}

	try {
		let output = pyodide.runPython(code.value);
		addOutputBox(code.value, output);
	} catch (err) {
		addOutputBox(code.value, err, true); // Display error in red
	}
}
function scrollToBottom() {
    window.scrollTo(0, document.body.scrollHeight);
}
function addOutputBox(inputCode, outputText, isError = false) {
	// Create a new div element for the output box
	var outputBox = document.createElement("div");
	outputBox.classList.add("output-box");
	
	// Add input code to the output box
	var inputElement = document.createElement("pre");
	inputElement.classList.add("input");
	inputElement.textContent = inputCode;
	outputBox.appendChild(inputElement);
	
	// Add output text to the output box
	var outputElement = document.createElement("pre");
	outputElement.classList.add("output");
	outputElement.textContent = outputText;
	if (isError) {
		outputElement.classList.add("error"); // Apply error styling if isError is true
	}
	outputBox.appendChild(outputElement);
	
	var contentBox = document.getElementById("content")
	// Append the output box to the main body
	contentBox.appendChild(outputBox);
	scrollToBottom();
}

// init Pyodide
async function main() {
	let pyodide = await loadPyodide();


	addOutputBox("loadPyodide()","Ready!")
	
	let response = await fetch("/tclish.zip"); // .zip, .whl, ...
	let buffer = await response.arrayBuffer();
	await pyodide.unpackArchive(buffer, "zip"); // by default, unpacks to the current dir
	pyodide.pyimport("tclish");
	addOutputBox("import tclish","ok")

	return pyodide;
}
let pyodideReadyPromise = main();

