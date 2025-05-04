-- CreateTable
CREATE TABLE "History" (
    "id" INTEGER NOT NULL,
    "MD5" TEXT NOT NULL,
    "SHA256" TEXT NOT NULL,
    "SSDEEP" TEXT NOT NULL,
    "Filetype" TEXT NOT NULL,
    "Filesize" TEXT NOT NULL,

    CONSTRAINT "History_pkey" PRIMARY KEY ("id")
);
