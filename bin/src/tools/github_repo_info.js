#!/usr/bin/env -S nix run nixpkgs#nodejs_22 --

/**
 * GitHub repository information tool - Gets basic information about a GitHub repository
 * 
 * @typedef {Object} Args
 * @property {string} owner - Repository owner/organization name (e.g., "kuzudb")
 * @property {string} repo - Repository name (e.g., "kuzu")
 * @property {boolean} [full=false] - Whether to get full information (false for basic info only)
 * @property {string} [format="json"] - Output format ("json", "text", or "csv")
 * @property {boolean} [raw=false] - Whether to return the raw response from GitHub
 */
exports.run = async function(args) {
  const https = require("node:https");
  const { owner, repo, full = false, format = "json", raw = false } = args;
  
  if (!owner || !owner.trim()) {
    console.error("Error: Repository owner name is not specified");
    process.exit(1);
  }
  
  if (!repo || !repo.trim()) {
    console.error("Error: Repository name is not specified");
    process.exit(1);
  }
  
  // Validate output format
  if (!["json", "text", "csv"].includes(format)) {
    console.error("Error: Invalid output format. Please specify json, text, or csv");
    process.exit(1);
  }
  
  try {
    const repoInfo = await fetchRepoInfo(owner, repo);
    
    if (raw) {
      console.log(JSON.stringify(repoInfo, null, 2));
      return;
    }
    
    // Filter info based on whether we want basic or full info
    const filteredInfo = full ? repoInfo : filterBasicInfo(repoInfo);
    
    // Output in the requested format
    switch (format) {
      case "json":
        console.log(JSON.stringify(filteredInfo, null, 2));
        break;
      case "text":
        outputAsText(filteredInfo);
        break;
      case "csv":
        outputAsCSV(filteredInfo);
        break;
    }
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
};

/**
 * Fetch repository information from GitHub API
 * @param {string} owner - Repository owner name
 * @param {string} repo - Repository name
 * @returns {Promise<Object>} - Object containing repository information
 */
async function fetchRepoInfo(owner, repo) {
  const https = require("node:https");
  
  return new Promise((resolve, reject) => {
    const options = {
      hostname: "api.github.com",
      path: `/repos/${owner}/${repo}`,
      method: "GET",
      headers: {
        "User-Agent": "GitHubRepoInfoTool/1.0",
        "Accept": "application/vnd.github.v3+json"
      }
    };
    
    const req = https.request(options, (res) => {
      let data = "";
      
      res.on("data", (chunk) => {
        data += chunk;
      });
      
      res.on("end", () => {
        if (res.statusCode === 200) {
          try {
            const repoInfo = JSON.parse(data);
            resolve(repoInfo);
          } catch (error) {
            reject(new Error(`JSON parsing error: ${error.message}`));
          }
        } else if (res.statusCode === 404) {
          reject(new Error(`Repository not found: ${owner}/${repo}`));
        } else {
          reject(new Error(`GitHub API error: ${res.statusCode} ${res.statusMessage}`));
        }
      });
    });
    
    req.on("error", (error) => {
      reject(new Error(`Network error: ${error.message}`));
    });
    
    req.end();
  });
}

/**
 * Extract only basic information from repository info
 * @param {Object} repoInfo - Full repository information from GitHub
 * @returns {Object} - Object containing only basic information
 */
function filterBasicInfo(repoInfo) {
  return {
    name: repoInfo.name,
    full_name: repoInfo.full_name,
    description: repoInfo.description,
    default_branch: repoInfo.default_branch,
    language: repoInfo.language,
    stargazers_count: repoInfo.stargazers_count,
    forks_count: repoInfo.forks_count,
    open_issues_count: repoInfo.open_issues_count,
    license: repoInfo.license?.name || "None",
    visibility: repoInfo.visibility,
    created_at: repoInfo.created_at,
    updated_at: repoInfo.updated_at,
    homepage: repoInfo.homepage,
    topics: repoInfo.topics || []
  };
}

/**
 * Output object as text
 * @param {Object} info - Repository information to output
 */
function outputAsText(info) {
  for (const [key, value] of Object.entries(info)) {
    // Special handling for arrays
    if (Array.isArray(value)) {
      console.log(`${key}: ${value.join(", ")}`);
    } else if (typeof value === "object" && value !== null) {
      // For objects, expand only one level
      console.log(`${key}:`);
      for (const [subKey, subValue] of Object.entries(value)) {
        console.log(`  ${subKey}: ${subValue}`);
      }
    } else {
      console.log(`${key}: ${value}`);
    }
  }
}

/**
 * Output object as CSV
 * @param {Object} info - Repository information to output
 */
function outputAsCSV(info) {
  const keys = Object.keys(info);
  const values = Object.values(info).map(value => {
    if (Array.isArray(value)) {
      return `"${value.join(",")}"`;
    } else if (typeof value === "string" && value.includes(",")) {
      return `"${value}"`;
    }
    return value;
  });
  
  console.log(keys.join(","));
  console.log(values.join(","));
}

// Entry point when this file is executed directly
if (require.main === module) {
  if (process.argv.length < 4) {
    console.error("Usage: github_repo_info.js <owner> <repo> [--full] [--format=json|text|csv] [--raw]");
    process.exit(1);
  }
  
  const args = {
    owner: process.argv[2],
    repo: process.argv[3],
    full: process.argv.includes("--full"),
    raw: process.argv.includes("--raw"),
    format: "json"
  };
  
  // Parse format specification
  const formatArg = process.argv.find(arg => arg.startsWith("--format="));
  if (formatArg) {
    const format = formatArg.split("=")[1];
    if (["json", "text", "csv"].includes(format)) {
      args.format = format;
    }
  }
  
  exports.run(args);
}
