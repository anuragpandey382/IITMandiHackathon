-- AlterTable
CREATE SEQUENCE history_id_seq;
ALTER TABLE "History" ALTER COLUMN "id" SET DEFAULT nextval('history_id_seq'),
ALTER COLUMN "Date" DROP DEFAULT,
ALTER COLUMN "Date" SET DATA TYPE TEXT;
ALTER SEQUENCE history_id_seq OWNED BY "History"."id";

-- AlterTable
ALTER TABLE "User" ADD COLUMN     "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
