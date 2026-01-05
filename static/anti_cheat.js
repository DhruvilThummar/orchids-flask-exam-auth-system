// Module 4: Anti-Cheating Logic

let violationCount = 0;
const maxViolations = parseInt(document.getElementById('max-violations').value);
const examId = document.getElementById('exam-id').value;

// Function to log violation to server
function logViolation() {
    violationCount++;
    
    // Send to backend
    fetch('/student/log_violation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            exam_id: examId
        })
    })
    .then(response => response.json())
    .then(data => {
        handleViolation(data.count);
    })
    .catch(error => console.error('Error logging violation:', error));
}

// Handle violation response
function handleViolation(count) {
    if (count >= maxViolations) {
        alert("CRITICAL WARNING: You have exceeded the maximum allowed tab switches. Your exam is being submitted automatically.");
        document.getElementById('exam-form').submit();
    } else if (count === 1) {
        alert("WARNING: Tab switching is not allowed. This is your 1st warning.");
    } else if (count === 2) {
        alert("STRONG WARNING: You have switched tabs again. One more switch and your exam will be auto-submitted.");
    } else {
        alert(`WARNING: Violation detected. Total violations: ${count}/${maxViolations}`);
    }
}

// 1. Detect Tab Switching / Focus Loss
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden') {
        logViolation();
    }
});

window.addEventListener('blur', function() {
    // Some browsers trigger blur when tab switches, others trigger visibilitychange
    // We use a small debounce or check to avoid double counting if both fire
    // For simplicity in this beginner project, we'll just log it
    logViolation();
});

// 2. Disable Right-Click, Copy, Paste
document.addEventListener('contextmenu', event => event.preventDefault());

document.addEventListener('copy', event => {
    event.preventDefault();
    alert("Copying is disabled during the exam.");
});

document.addEventListener('paste', event => {
    event.preventDefault();
    alert("Pasting is disabled during the exam.");
});

// 3. Warning on Refresh
window.onbeforeunload = function() {
    return "Are you sure you want to leave? Your progress may be lost.";
};
