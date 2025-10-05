Param(
    [string]$RepoName = "obsidian-ai-organizer",
    [string]$User = "flyswxf"
)

Write-Host "🚀 Publishing repository to GitHub as $User/$RepoName" -ForegroundColor Cyan

if (-not $env:GITHUB_TOKEN) {
    Write-Error "GITHUB_TOKEN 未设置。请先在当前终端设置：`setx GITHUB_TOKEN <your_token>`，然后重启终端。"
    exit 1
}

# Create repository via GitHub API
$headers = @{ 
    Authorization = "token $($env:GITHUB_TOKEN)"; 
    "User-Agent" = "pwsh-publish-script"
}

$body = @{ 
    name = $RepoName; 
    description = "AI-powered Obsidian organizer and image renamer"; 
    private = $false 
} | ConvertTo-Json

Write-Host "📦 Creating GitHub repository..." -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod -Method Post -Uri "https://api.github.com/user/repos" -Headers $headers -ContentType "application/json" -Body $body
    Write-Host "✅ Repository created: https://github.com/$User/$RepoName" -ForegroundColor Green
} catch {
    Write-Warning "⚠️ 创建仓库失败，可能已存在或令牌权限不足。继续尝试配置远程并推送。"
}

# Configure git remote
Write-Host "🔧 Configuring git remote..." -ForegroundColor Yellow
try {
    git remote remove origin 2>$null
} catch {}
git remote add origin "https://github.com/$User/$RepoName.git"

# Set default branch and push with token authentication embedded in URL
git branch -M main
Write-Host "⬆️ Pushing to GitHub..." -ForegroundColor Yellow
git push -u "https://$($env:GITHUB_TOKEN)@github.com/$User/$RepoName.git" main

Write-Host "🎉 Done. Repo: https://github.com/$User/$RepoName" -ForegroundColor Green