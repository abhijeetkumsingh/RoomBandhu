import { initializeApp } from "https://www.gstatic.com/firebasejs/11.0.0/firebase-app.js";

import {
    getAuth,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    GoogleAuthProvider,
    signInWithPopup,
    sendEmailVerification,
    signOut
} from "https://www.gstatic.com/firebasejs/11.0.0/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyD1s78eU7xpRh54KYzBZoEsBg0VnsIizSg",
  authDomain: "roombandhu-cb973.firebaseapp.com",
  projectId: "roombandhu-cb973",
  storageBucket: "roombandhu-cb973.firebasestorage.app",
  messagingSenderId: "1096156536641",
  appId: "1:1096156536641:web:4d37d3a43383d499b3cbc0"
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);

export {
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    GoogleAuthProvider,
    signInWithPopup,
    sendEmailVerification,
    signOut
};