// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
let vscode;
try {
  vscode = require('vscode');
} catch (error) {
  console.log('This extension is meant to be run within VS Code, not directly with Node.js');
  console.log('To test this extension, launch it from VS Code using F5 or the Run Extension command');
  process.exit(0);
}

// Import required Node.js modules for file operations and process spawning
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { exec } = require('child_process');
const os = require('os');

// Panels will be stored here so they can be disposed properly
let troubleshooterPanel = undefined;
let currentPanelView = undefined;

/**
 * Execute a shell command and return its output as a Promise
 * @param {string} cmd - The command to execute
 * @returns {Promise<string>} - A promise that resolves with stdout or rejects with an error
 */
function executeCommand(cmd) {
  return new Promise((resolve, reject) => {
    exec(cmd, (error, stdout, stderr) => {
      if (error) {
        reject(`Error: ${error.message}\n${stderr}`);
        return;
      }
      resolve(stdout);
    });
  });
}

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "matlab-troubleshooter" is now active!');
	
	// Log more activation information
	console.log('Extension path:', context.extensionPath);
	console.log('Extension URI:', context.extensionUri.toString());
	
	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	const disposable = vscode.commands.registerCommand('matlab-troubleshooter.helloWorld', function () {
		// The code you place here will be executed every time your command is executed

		// Display a message box to the user
		vscode.window.showInformationMessage('Hello World from Matlab_Troubleshooter!');
	});

	context.subscriptions.push(disposable);

	// Register WebView View Provider for the sidebar - with explicit ID matching package.json
	const provider = new MatlabTroubleshooterViewProvider(context.extensionUri, context.extensionPath);
	
	// Register the view provider with the extension
	try {
		const registration = vscode.window.registerWebviewViewProvider(
			'matlab-troubleshooter-panel',
			provider,
			{
				webviewOptions: {
					retainContextWhenHidden: true
				}
			}
		);
		context.subscriptions.push(registration);
		console.log('Webview provider registered successfully');
	} catch (error) {
		console.error('Failed to register webview provider:', error);
		vscode.window.showErrorMessage('Failed to initialize MATLAB Troubleshooter panel: ' + error.message);
	}

	// Command to show the troubleshooter panel 
	const showTroubleshooterCommand = vscode.commands.registerCommand('matlab-troubleshooter.showTroubleshooterPanel', () => {
		try {
			// Show message to confirm the command was triggered
			vscode.window.showInformationMessage('Opening MATLAB Troubleshooter panel');
			// Focus the view 
			vscode.commands.executeCommand('workbench.view.extension.matlab-troubleshooter-sidebar');
		} catch (error) {
			console.error('Error showing troubleshooter panel:', error);
			vscode.window.showErrorMessage('Failed to open MATLAB Troubleshooter panel: ' + error.message);
		}
	});

	context.subscriptions.push(showTroubleshooterCommand);
	
	// Auto-show the panel on activation (only during development)
	setTimeout(() => {
		vscode.commands.executeCommand('workbench.view.extension.matlab-troubleshooter-sidebar')
			.then(() => console.log('Panel auto-displayed'))
			.catch(err => console.error('Failed to auto-display panel:', err));
	}, 2000);

	// Log when a MATLAB file is opened, confirming the language activation is working
	vscode.window.onDidChangeActiveTextEditor((editor) => {
		if (editor && editor.document.languageId === 'matlab') {
			console.log('MATLAB file detected and extension activated');
		}
	});
}

/**
 * WebView Provider for the MATLAB Troubleshooter panel
 */
class MatlabTroubleshooterViewProvider {
	constructor(extensionUri, extensionPath) {
		this.extensionUri = extensionUri;
		this.sessionId = null;
		this.extensionPath = extensionPath;
		
		// Path to the Python virtual environment
		this.pythonEnvDir = path.join(this.extensionPath, 'Matlab_extension', '.venv');
		
		// Check if we're on Windows or Unix-like
		this.isWindows = process.platform === 'win32';
		
		// Path to the Python executable in the virtual environment
		this.pythonPath = this.isWindows 
			? path.join(this.pythonEnvDir, 'Scripts', 'python.exe')
			: path.join(this.pythonEnvDir, 'bin', 'python');
			
		// Path to the requirements.txt file
		this.requirementsPath = path.join(this.extensionPath, 'Matlab_extension', 'requirements.txt');
	}
		/**
	 * Generates a unique session ID
	 * @returns {string} - A unique session ID
	 */
	generateSessionId() {
		// Create a random session ID using timestamp and random string
		const timestamp = Date.now();
		const randomStr = Math.random().toString(36).substring(2, 10);
		this.sessionId = `session_${timestamp}_${randomStr}`;
		return this.sessionId;
	}

	/**
	 * Gets the current session ID or generates a new one
	 * @returns {string} - The current session ID
	 */
	getSessionId() {
		if (!this.sessionId) {
			return this.generateSessionId();
		}
		return this.sessionId;
	}
	/**
	 * Called when a view first becomes visible
	 * @param {vscode.WebviewView} webviewView 
	 */
	resolveWebviewView(webviewView, context, token) {
		// Request a larger initial size for the webview
		webviewView.webview.options = {
			enableScripts: true,
			localResourceRoots: [this.extensionUri]
		};

		// Try to increase the initial size
		if (webviewView.visible) {
			// Set a minimum width
			webviewView.webview.postMessage({ 
				command: 'initialize',
				minWidth: 100 // Suggest a larger width
			});
		}

		// Set the HTML content of the webview
		webviewView.webview.html = this.getHtmlContent();

		// Handle messages from the webview
		webviewView.webview.onDidReceiveMessage(message => {
			switch (message.command) {
				case 'troubleshoot':  //command
					// Process the MATLAB code and provide troubleshooting feedback
					this.troubleshootMatlabCode(message.code, webviewView);
					break;
			}
		});

		// Store reference to current panel
		currentPanelView = webviewView;
	}

	/**
	 * Process MATLAB code and provide troubleshooting feedback
	 * @param {string} code - The MATLAB code to troubleshoot
	 * @param {vscode.WebviewView} webviewView - The webview to update with results
	 * @param {string|null} imagePath - Optional path to an image file
	 */
	async troubleshootMatlabCode(code, webviewView, imagePath = null) {
		// Inform the user that we're processing their request
		webviewView.webview.postMessage({
			command: 'troubleshootResults',
			results: `<p>Analyzing your MATLAB code...</p><p>This might take a moment...</p>`,
			status: 'processing'
		});
		
		try {
			// Make API call to the external endpoint
			const apiEndpoint = "https://bda1-2409-40d7-e8-dce-4026-1aab-2ef2-879d.ngrok-free.app/chat/form";
			
			// To match the Python implementation, we need to use FormData with 'files' parameter
			const https = require('https');
			const querystring = require('querystring');
			const fs = require('fs');
			
			// Create a boundary for multipart form data
			const boundary = '----WebKitFormBoundary' + Math.random().toString(16).substr(2);
			
			// Prepare the form data parts
			let formBody = '';

			// Add the query part
			formBody += `--${boundary}\r\n`;
			formBody += 'Content-Disposition: form-data; name="prompt"\r\n\r\n';
			formBody += code + '\r\n';

			// Add the session ID part
			formBody += `--${boundary}\r\n`;
			formBody += 'Content-Disposition: form-data; name="sessionid"\r\n\r\n';
			formBody += this.sessionId || this.generateSessionId() + '\r\n';

			// If image path is provided, add the image part
			let fileBuffer = null;
			let fileStat = null;
			
			if (imagePath && fs.existsSync(imagePath)) {
				fileBuffer = fs.readFileSync(imagePath);
				fileStat = fs.statSync(imagePath);
				const fileName = path.basename(imagePath);
				
				formBody += `--${boundary}\r\n`;
				formBody += `Content-Disposition: form-data; name="image"; filename="${fileName}"\r\n`;
				formBody += 'Content-Type: image/png\r\n\r\n';
				
				// We'll append the binary file data later
			}
			
			// Options for the HTTP request
			const options = {
				method: 'POST',
				headers: {
					'Content-Type': `multipart/form-data; boundary=${boundary}`,
				}
			};
			
			// Create promise to handle the request
			const response = await new Promise((resolve, reject) => {
				const req = https.request(apiEndpoint, options, (res) => {
					let data = '';
					
					// Handle response data
					res.on('data', (chunk) => {
						data += chunk;
					});
					
					// When response is complete
					res.on('end', () => {
						if (res.statusCode >= 200 && res.statusCode < 300) {
							resolve(data);
						} else {
							console.error(`API error response: ${res.statusCode} - ${data}`);
							reject(new Error(`API request failed with status code ${res.statusCode}: ${data}`));
						}
					});
				});
				
				// Handle request errors
				req.on('error', (error) => {
					console.error("Request error:", error);
					reject(error);
				});
				
				// Write the form data parts
				req.write(formBody);
				
				// If we have a file, write the binary data
				if (fileBuffer) {
					req.write(fileBuffer);
					req.write('\r\n');
				}
				
				// End the form data
				req.write(`--${boundary}--\r\n`);
				req.end();
			});
			
			// Parse the response
			let result;
			try {
				result = JSON.parse(response);
				console.log("Received API response:", JSON.stringify(result).substring(0, 500) + "...");
				
				// Format the result according to the Python implementation's expected structure
				const formattedResult = {
					final_response: result.final_response || "No response received from server",
					refrence_links: Array.isArray(result.reference_links) ? result.reference_links.map(ref => ref.url) : [],
					relevant_docs: Array.isArray(result.relevant_docs) ? 
						result.relevant_docs.sort((a, b) => b.score - a.score).map(doc => doc.content_preview) : []
				};
				
				console.log("Formatted result:", JSON.stringify(formattedResult));
				// Format the result for display
				const htmlResult = this.formatTroubleshootingResult(formattedResult);
				console.log("HTML Result:", htmlResult);
				// Send the results back to the webview
				webviewView.webview.postMessage({
					command: 'troubleshootResults',
					results: htmlResult,
					rawResult: formattedResult,
					status: 'success'
				});
				
			} catch (error) {
				console.error("Error parsing JSON response:", error);
				// If not JSON, use as text
				webviewView.webview.postMessage({
					command: 'troubleshootResults',
					results: `<h3 style="color:red">Error parsing response</h3><p>${error.message}</p><pre>${response}</pre>`,
					status: 'error'
				});
			}
			
		} catch (error) {
			console.error('Error analyzing MATLAB code:', error);
			webviewView.webview.postMessage({
				command: 'troubleshootResults',
				results: `
					<h3 style="color:red">Error analyzing code</h3>
					<p>${error.message}</p>
				`,
				status: 'error'
			});
		}
	}
	/**
	 * Formats the troubleshooting result with better HTML styling
	 * @param {string|object} result - The raw troubleshooting result
	 * @returns {string} - Formatted HTML
	 */
	formatTroubleshootingResult(result) {
		// Parse result if it's a string
		let parsedResult = result;
		if (typeof result === 'string') {
			try {
				parsedResult = JSON.parse(result);
			} catch (e) {
				console.log('Not a JSON result, using as text');
			}
		}
		
		// Extract data from the API response structure
		let finalResponse = '';
		let referenceLinks = [];
		let relevantDocs = [];
		
		// Check if result has the expected structure
		if (parsedResult) {
			finalResponse = parsedResult.final_response || '';
			referenceLinks = parsedResult.refrence_links || []; // Note: handling the API's spelling "refrence"
			relevantDocs = parsedResult.relevant_docs || [];
		}
		
		// If we don't have a structured response, use the raw result as text
		if (!finalResponse) {
			finalResponse = typeof result === 'string' ? result : JSON.stringify(result);
		}
		
		// Convert markdown to HTML for the final response
		const formattedFinalResponse = this.convertMarkdownToHtml(finalResponse);
		
		// Format reference links as HTML
		let formattedReferences = '';
		if (referenceLinks && referenceLinks.length > 0) {
			formattedReferences = referenceLinks.map(link => 
				`<a href="${link}" target="_blank">${link}</a>`
			).join('<br>');
		}
		
		// Format relevant docs
		let formattedRelevantDocs = '';
		if (relevantDocs && relevantDocs.length > 0) {
			formattedRelevantDocs = '<ul>' + 
				relevantDocs.map(doc => `<li>${this.convertMarkdownToHtml(doc)}</li>`).join('') + 
				'</ul>';
		}
		
		// Build the formatted HTML with proper headings
		return `
			<div class="troubleshooting-result">
				<h2>MATLAB Response</h2>
				
				<h3>Response:</h3>
				<div class="section final-response">
					${formattedFinalResponse || 'No analysis provided.'}
				</div>
				
				<h3>Reference Links:</h3>
				<div class="section references">
					${formattedReferences || 'No reference links available.'}
				</div>
				
				<h3>Relevant Documentation:</h3>
				<div class="section relevant-docs">
					${formattedRelevantDocs || 'No relevant documentation found.'}
				</div>
			</div>
		`;
	}

	/**
	 * Converts markdown text to HTML
	 * @param {string} markdown - The markdown text to convert
	 * @returns {string} - The HTML representation
	 */
	convertMarkdownToHtml(markdown) {
		if (!markdown) return '';
		
		// Handle headings
		let html = markdown
			.replace(/^# (.*$)/gm, '<h1>$1</h1>')
			.replace(/^## (.*$)/gm, '<h2>$1</h2>')
			.replace(/^### (.*$)/gm, '<h3>$1</h3>')
			.replace(/^#### (.*$)/gm, '<h4>$1</h4>')
			.replace(/^##### (.*$)/gm, '<h5>$1</h5>')
			.replace(/^###### (.*$)/gm, '<h6>$1</h6>');
		
		// Handle code blocks (```code```)
		html = html.replace(/```matlab([\s\S]*?)```/g, '<pre class="code-block matlab">$1</pre>');
		html = html.replace(/```([\s\S]*?)```/g, '<pre class="code-block">$1</pre>');
		
		// Handle inline code (`code`)
		html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
		
		// Handle bold (**text**)
		html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
		
		// Handle italic (*text*)
		html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
		
		// Handle lists
		html = html.replace(/^\s*\d+\.\s+(.*$)/gm, '<li>$1</li>');
		html = html.replace(/^\s*[-*]\s+(.*$)/gm, '<li>$1</li>');
		
		// Wrap ordered and unordered lists properly
		// This is simplistic and might need improvement
		html = html.replace(/<li>(.*)<\/li>\n<li>/g, '<li>$1</li>\n<li>');
		
		// Handle links [text](url)
		html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
		
		// Handle paragraphs (simplified)
		html = html.replace(/\n\s*\n/g, '</p><p>');
		
		// Wrap the content in paragraphs if it's not already wrapped in HTML tags
		if (!/<[a-z][\s\S]*>/i.test(html)) {
			html = `<p>${html}</p>`;
		}
		
		// Fix any broken paragraphs
		html = html.replace(/<\/p><p><\/p>/g, '</p>');
		
		return html;
	}
	/**
	 * Generate the HTML content for the webview
	 */
	getHtmlContent() {
		return `
			<!DOCTYPE html>
			<html lang="en">
			<head>
				<meta charset="UTF-8">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<title>MATLAB Troubleshooter</title>
				<style>
					:root {
						--panel-min-width: 400px; /* Minimum width suggestion */
					}
					
					body {
						font-family: var(--vscode-font-family);
						color: var(--vscode-editor-foreground);
						background-color: var(--vscode-editor-background);
						padding: 16px;
						min-width: var(--panel-min-width);
						overflow-x: hidden;
					}
					
					.container {
						display: flex;
						flex-direction: column;
						height: 100%;
						min-width: 100%;
					}
					
					.header {
						font-size: 1.3em;
						font-weight: bold;
						margin-bottom: 16px;
					}
					
					textarea {
						width: calc(100% - 12px);
						height: 180px; /* Increased height */
						margin-bottom: 16px;
						background-color: var(--vscode-input-background);
						color: var(--vscode-input-foreground);
						border: 1px solid var(--vscode-input-border);
						padding: 8px;
						resize: vertical;
						border-radius: 3px;
						font-family: var(--vscode-editor-font-family);
						font-size: var(--vscode-editor-font-size);
					}
					
					button {
						padding: 10px 20px;
						background-color: var(--vscode-button-background);
						color: var(--vscode-button-foreground);
						border: none;
						cursor: pointer;
						border-radius: 3px;
						font-weight: 500;
						margin-bottom: 16px;
					}
					
					button:hover {
						background-color: var(--vscode-button-hoverBackground);
					}
					
					.results {
						margin-top: 16px;
						padding: 12px;
						border: 1px solid var(--vscode-panel-border);
						border-radius: 3px;
						flex-grow: 1;
						overflow: auto;
						overflow-wrap: break-word;
						min-height: 200px; /* Ensure it has some height even when empty */
					}
					
					pre {
						background-color: var(--vscode-editor-inactiveSelectionBackground);
						padding: 12px;
						overflow: auto;
						border-radius: 3px;
						font-family: var(--vscode-editor-font-family);
						font-size: var(--vscode-editor-font-size);
					}
					
					.troubleshooting-result h3 {
						margin-top: 20px;
						margin-bottom: 10px;
						color: var(--vscode-editorLink-activeForeground);
						border-bottom: 1px solid var(--vscode-panel-border);
						padding-bottom: 5px;
					}
					
					.troubleshooting-result .section {
						margin-bottom: 20px;
					}
					
					.code-block {
						background-color: var(--vscode-editor-inactiveSelectionBackground);
						padding: 12px;
						border-radius: 3px;
						white-space: pre-wrap;
					}
					
					.code-block.matlab {
						border-left: 3px solid var(--vscode-activityBarBadge-background);
					}

					/* Make sure the panel tries to use maximum available space */
					html, body {
						width: 100%;
						height: 100%;
						margin: 0;
						padding: 0;
						box-sizing: border-box;
					}
					body {
						padding: 16px;
						box-sizing: border-box;
					}
					
					.spinner {
						width: 40px;
						height: 40px;
						margin: 20px auto;
						border: 3px solid rgba(255,255,255,.3);
						border-radius: 50%;
						border-top-color: var(--vscode-button-background);
						animation: spin 1s ease-in-out infinite;
					}
					
					@keyframes spin {
						to { transform: rotate(360deg); }
					}
				</style>
			</head>
			<body>
				<div class="container">
					<div class="header">MATLAB Troubleshooter</div>
					<textarea id="code-input" placeholder="Paste your MATLAB code here for troubleshooting..."></textarea>
					<button id="troubleshoot-button">Troubleshoot</button>
					<div class="results" id="results">
						Results will appear here...
					</div>
				</div>

				<script>
					// Get references to the elements
					const vscode = acquireVsCodeApi();
					const codeInput = document.getElementById('code-input');
					const troubleshootButton = document.getElementById('troubleshoot-button');
					const results = document.getElementById('results');

					// Try to request more space for the panel
					function requestLargerPanel() {
						// This doesn't directly control the size but hints to VS Code
						document.body.style.minWidth = '400px';
						document.documentElement.style.minWidth = '400px';
					}
					
					// Run on load
					requestLargerPanel();

					// Listen for messages from the extension
					window.addEventListener('message', event => {
						const message = event.data;
						
						switch (message.command) {
							case 'troubleshootResults':
								// Handle results with status
								switch(message.status) {
									case 'processing':
										results.innerHTML = message.results + '<div class="spinner"></div>';
										troubleshootButton.disabled = true;
										break;
										
									case 'success':
										results.innerHTML = message.results;
										troubleshootButton.disabled = false;
										break;
										
									case 'error':
										results.innerHTML = message.results;
										troubleshootButton.disabled = false;
										break;
										
									default:
										results.innerHTML = message.results;
										troubleshootButton.disabled = false;
								}
								break;
								
							case 'initialize':
								// Extension is trying to set size preferences
								if (message.minWidth) {
									document.body.style.minWidth = message.minWidth + 'px';
									document.documentElement.style.minWidth = message.minWidth + 'px';
								}
								break;
						}
					});

					// Add event listener for the troubleshoot button
					troubleshootButton.addEventListener('click', () => {
						const code = codeInput.value;
						if (code.trim() === '') {
							results.innerHTML = 'Please enter MATLAB code to troubleshoot.';
							return;
						}

						// Send message to extension
						vscode.postMessage({
							command: 'troubleshoot',
							code: code
						});

						results.innerHTML = '<p>Analyzing your code...</p><div class="spinner"></div>';
						troubleshootButton.disabled = true;
					});

					// Make sure we start with focus on the input
					window.addEventListener('load', () => {
						setTimeout(() => codeInput.focus(), 300);
					});
				</script>
			</body>
			</html>
		`;
	}
}

// This method is called when your extension is deactivated
function deactivate() {
	// Clean up resources
	if (troubleshooterPanel) {
		troubleshooterPanel.dispose();
	}
}

module.exports = {
	activate,
	deactivate
}
