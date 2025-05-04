/*
  Warnings:

  - You are about to drop the column `Filesize` on the `History` table. All the data in the column will be lost.
  - You are about to drop the column `Filetype` on the `History` table. All the data in the column will be lost.
  - You are about to drop the column `MD5` on the `History` table. All the data in the column will be lost.
  - You are about to drop the column `SHA256` on the `History` table. All the data in the column will be lost.
  - You are about to drop the column `SSDEEP` on the `History` table. All the data in the column will be lost.
  - You are about to drop the column `createdAt` on the `User` table. All the data in the column will be lost.
  - Added the required column `fileName` to the `History` table without a default value. This is not possible if the table is not empty.
  - Added the required column `mal` to the `History` table without a default value. This is not possible if the table is not empty.
  - Added the required column `userId` to the `History` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "History" DROP COLUMN "Filesize",
DROP COLUMN "Filetype",
DROP COLUMN "MD5",
DROP COLUMN "SHA256",
DROP COLUMN "SSDEEP",
ADD COLUMN     "Date" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN     "fileName" TEXT NOT NULL,
ADD COLUMN     "mal" INTEGER NOT NULL,
ADD COLUMN     "userId" INTEGER NOT NULL;

-- AlterTable
ALTER TABLE "User" DROP COLUMN "createdAt";

-- AddForeignKey
ALTER TABLE "History" ADD CONSTRAINT "History_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
