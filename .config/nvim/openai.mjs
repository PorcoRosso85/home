#!/usr/bin/env node

// https://zenn.dev/yaasita/articles/8e1ee2f7a7603e
"use strict";
import { Configuration, OpenAIApi } from "openai";
import fs from "fs";
const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY,
});
const openai = new OpenAIApi(configuration);
const input = fs.readFileSync("/dev/stdin", "utf8");
const response = await openai.createCompletion({
  model: "text-davinci-002",
  prompt: input,
  temperature: 0,
  max_tokens: 1000,
});
console.log(response.data.choices[0].text);
