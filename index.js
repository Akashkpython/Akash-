import 'dotenv/config';
import { GoogleGenerativeAI } from "@google/generative-ai";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

async function run() {
  const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

  const prompt = "Hello Gemini! Tell me a fun fact about JavaScript.";
  const result = await model.generateContent(prompt);

  console.log(result.response.text());
}

run();