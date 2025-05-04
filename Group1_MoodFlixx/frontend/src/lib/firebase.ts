// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics, isSupported } from "firebase/analytics";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyArG_6XxCDu2CBoUBTvB2hiW6hdpmf3ddo",
  authDomain: "moodflixx-cs671.firebaseapp.com",
  projectId: "moodflixx-cs671",
  storageBucket: "moodflixx-cs671.firebasestorage.app",
  messagingSenderId: "813285590607",
  appId: "1:813285590607:web:e7d68f5cf87894108f4c3a",
  measurementId: "G-66MSBPB6JN",
};

// Initialize Firebase

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleAuthProvider = new GoogleAuthProvider();
const db = getFirestore(app);

let analytics: ReturnType<typeof getAnalytics> | undefined = undefined;

if (typeof window !== "undefined") {
  await isSupported().then((supported) => {
    if (supported) {
      analytics = getAnalytics(app);
    }
  });
}

export { app, auth, analytics, googleAuthProvider, db };
