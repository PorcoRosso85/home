import { defineScript } from "rwsdk/worker";
import { db, setupDb } from "@/db";
import { logInfo } from "@/utils/logger";

export default defineScript(async ({ env }) => {
  await setupDb(env);

  await db.$executeRawUnsafe(`\
    DELETE FROM User;
    DELETE FROM sqlite_sequence;
  `);

  await db.user.create({
    data: {
      id: "1",
      username: "testuser",
    },
  });

  logInfo("seed-complete", "🌱 Finished seeding");
});
