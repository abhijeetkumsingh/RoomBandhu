
import {
    auth,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    GoogleAuthProvider,
    signInWithPopup,
    sendEmailVerification,
    signOut
} from "./firebase.js";

// HTML elements
const loginForm = document.getElementById("firebaseLoginForm");
const registerForm = document.getElementById("firebaseRegisterForm");
const googleButton = document.getElementById("googleSignInBtn");

// Display messages
function showMessage(message, type = "error") {
    let messageBox = document.getElementById("authMessage");

    if (!messageBox) {
        messageBox = document.createElement("div");
        messageBox.id = "authMessage";

        const authCard = document.querySelector(".auth-card");
        const divider = document.querySelector(".divider");

        if (authCard && divider) {
            divider.insertAdjacentElement("afterend", messageBox);
        } else if (authCard) {
            authCard.prepend(messageBox);
        }
    }

    messageBox.textContent = message;
    messageBox.style.padding = "12px";
    messageBox.style.margin = "12px 0";
    messageBox.style.borderRadius = "8px";
    messageBox.style.fontSize = "14px";
    messageBox.style.background =
        type === "success" ? "#dcfce7" : "#fee2e2";
    messageBox.style.color =
        type === "success" ? "#166534" : "#991b1b";
}

function getFirebaseError(error) {
    const messages = {
        "auth/email-already-in-use": "This email is already registered.",
        "auth/invalid-email": "Please enter a valid email address.",
        "auth/weak-password": "Password must be at least 6 characters.",
        "auth/invalid-credential": "Invalid email or password.",
        "auth/user-not-found": "No account found with this email.",
        "auth/wrong-password": "Incorrect password.",
        "auth/popup-closed-by-user": "Google sign-in was cancelled.",
        "auth/popup-blocked": "Please allow popups for Google sign-in.",
        "auth/network-request-failed": "Network error. Please try again."
    };

    return messages[error.code] || error.message || "Something went wrong.";
}

// Get CSRF token
function getCSRFToken() {
    const tokenInput = document.querySelector(
        'input[name="csrf_token"]'
    );

    return tokenInput ? tokenInput.value : "";
}

// Create Flask session after Firebase authentication
async function createFlaskSession(user, extraData = {}) {
    const idToken = await user.getIdToken();

    const response = await fetch("/auth/firebase/session", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({
            idToken: idToken,
            ...extraData
        })
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(data.error || "Unable to create session.");
    }

    window.location.href = data.redirect || "/dashboard";
}

// Email and Password Registration
if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const name = registerForm.querySelector(
            'input[name="name"]'
        ).value.trim();

        const email = registerForm.querySelector(
            'input[name="email"]'
        ).value.trim();

        const phone = registerForm.querySelector(
            'input[name="phone"]'
        ).value.trim();

        const password = registerForm.querySelector(
            'input[name="password"]'
        ).value;

        const confirmPassword = registerForm.querySelector(
            'input[name="confirm_password"]'
        ).value;

        if (!name || !email || !password) {
            showMessage("Please fill all required fields.");
            return;
        }

        if (password.length < 6) {
            showMessage("Password must be at least 6 characters.");
            return;
        }

        if (password !== confirmPassword) {
            showMessage("Passwords do not match.");
            return;
        }

        try {
            const result = await createUserWithEmailAndPassword(
                auth,
                email,
                password
            );

            await sendEmailVerification(result.user);

            await signOut(auth);

            showMessage(
                "Account created! Please check your email and verify your email address before logging in.",
                "success"
            );

            registerForm.reset();

        } catch (error) {
            console.error("Registration error:", error);
            showMessage(getFirebaseError(error));
        }
    });
}

// Email and Password Login
if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const email = loginForm.querySelector(
            'input[name="email"]'
        ).value.trim();

        const password = loginForm.querySelector(
            'input[name="password"]'
        ).value;

        try {
            const result = await signInWithEmailAndPassword(
                auth,
                email,
                password
            );

            if (!result.user.emailVerified) {
                await sendEmailVerification(result.user);
                await signOut(auth);

                showMessage(
                    "Please verify your email first. A verification email has been sent."
                );
                return;
            }

            await createFlaskSession(result.user);

        } catch (error) {
            console.error("Login error:", error);

            // Keep legacy SQL login available for existing accounts.
            if (
                error.code === "auth/user-not-found" ||
                error.code === "auth/invalid-credential" ||
                error.code === "auth/wrong-password"
            ) {
                loginForm.submit();
                return;
            }

            showMessage(getFirebaseError(error));
        }
    });
}

// Google Sign-In
if (googleButton) {
    googleButton.addEventListener("click", async () => {
        try {
            const provider = new GoogleAuthProvider();

            const result = await signInWithPopup(auth, provider);

            await createFlaskSession(result.user);

        } catch (error) {
            console.error("Google sign-in error:", error);
            showMessage(getFirebaseError(error));
        }
    });
}
