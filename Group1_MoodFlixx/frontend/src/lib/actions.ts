import {
  addDoc,
  collection,
  getDocs,
  query,
  updateDoc,
  where,
} from "firebase/firestore";
import { auth, db } from "@/lib/firebase";
import { onAuthStateChanged, type User } from "firebase/auth";
import type { MovieType } from "@/lib/movies";
import toast from "react-hot-toast";
import { redirect } from "next/navigation";

export function getCurrentUser(): Promise<User | null> {
  return new Promise((resolve) => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      unsubscribe();
      resolve(user);
    });
  });
}

export async function getPreferences() {
  const user = await getCurrentUser();

  if (!user) {
    toast.error("No user is signed in.");
    redirect("/login");
  }
  console.log("User ID: ", user.uid);

  const q = query(collection(db, "accounts"), where("user_id", "==", user.uid));
  const querySnapshot = await getDocs(q);

  if (querySnapshot.empty) {
    console.log("No matching documents.");
    return;
  }

  const accDoc = querySnapshot.docs[0];
  return accDoc?.data();
}

export async function addAccount({
  loc,
  lang,
  currHistory,
}: {
  loc: string;
  lang: string;
  currHistory: MovieType[];
}) {
  const user = await getCurrentUser();

  if (!user) {
    toast.error("No user is signed in.");
    redirect("/login");
  }

  const updatedData = {
    user_id: user.uid,
    language: lang,
    location: loc,
    history: currHistory,
    genre: [],
    cast: [],
    mood: [],
  };

  const q = query(collection(db, "accounts"), where("user_id", "==", user.uid));
  const querySnapshot = await getDocs(q);

  if (querySnapshot.empty) {
    try {
      const docRef = await addDoc(collection(db, "accounts"), updatedData);
      console.log("Document written with ID: ", docRef.id);
    } catch (e) {
      toast.error("Error adding document. Check console");
      console.log(e);
    }
    return;
  }

  const accDoc = querySnapshot.docs[0];
  const docRef = accDoc?.ref;

  if (!docRef) {
    console.error("No document reference found.");
    return;
  }
  await updateDoc(docRef, updatedData);

  console.log("Document updated with ID: ", docRef.id);
}

export async function getHistory() {
  const user = await getCurrentUser();

  if (!user) {
    toast.error("No user is signed in.");
    redirect("/login");
  }

  const q = query(collection(db, "accounts"), where("user_id", "==", user.uid));
  const querySnapshot = await getDocs(q);

  if (querySnapshot.empty) {
    console.log("No matching documents.");
    return;
  }

  const accDoc = querySnapshot.docs[0];
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const history: MovieType[] = accDoc?.data().history;

  if (!history) {
    console.log("No history found.");
    return;
  }

  return history;
}

export async function getPlaylistRecommendations() {
  const user = await getCurrentUser();

  if (!user) {
    toast.error("No user is signed in.");
    redirect("/login");
  }

  const q = query(collection(db, "accounts"), where("user_id", "==", user.uid));
  const querySnapshot = await getDocs(q);

  if (querySnapshot.empty) {
    console.log("No matching documents.");
    return;
  }

  const accDoc = querySnapshot.docs[0];

  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const history = accDoc?.data().history;

  if (!history) {
    console.log("No history found.");
    return;
  }

  // eslint-disable-next-line @typescript-eslint/no-unsafe-call,@typescript-eslint/no-unsafe-member-access,@typescript-eslint/no-unsafe-assignment
  const playlist = history.map((el: { title: string; rating: number }) => ({
    title: el.title,
    rating: el.rating,
  }));

  console.log(playlist);

  try {
    console.log("Sending data:", JSON.stringify(playlist));

    const response = await fetch("http://localhost:8000/api/playlist", {
      // change to recommendations
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ ratings: playlist }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Server response:", response.status, errorText);
      throw new Error(
        `HTTP error! Status: ${response.status}. Details: ${errorText}`,
      );
    }

    const data = await response.json();

    return data;
  } catch (error) {
    toast.error("Error fetching movie recommendations. Check console");
    console.log(error);
    throw error;
  }
}

export const rateMovie = async ({
  movie,
  rating,
}: {
  movie: MovieType;
  rating: number;
}) => {
  const user = await getCurrentUser();
  if (!user) {
    toast.error("No user is signed in.");
    redirect("/login");
  }

  const q = query(collection(db, "accounts"), where("user_id", "==", user.uid));
  const querySnapshot = await getDocs(q);

  if (querySnapshot.empty) {
    console.error("No account document found for user.");
    return;
  }

  const accDoc = querySnapshot.docs[0];
  const docRef = accDoc.ref;
  const prevData = accDoc.data();

  const history = prevData.history;

  if (!Array.isArray(history)) {
    console.error("History is not an array.");
    return;
  }

  let updated = false;
  const updatedHistory = history.map((el: MovieType & { rating: number }) => {
    if (el.title === movie.title) {
      updated = true;
      return { ...movie, rating }; // overwrite with new movie data and updated rating
    }
    return el;
  });

  if (!updated) {
    updatedHistory.push({
      ...movie,
      rating,
    });
  }

  const updatedData = {
    ...prevData,
    history: updatedHistory,
  };

  try {
    await updateDoc(docRef, updatedData);
    console.log("Document updated with ID: ", docRef.id);
  } catch (e) {
    console.error("Failed to update document:", e);
  }
};
