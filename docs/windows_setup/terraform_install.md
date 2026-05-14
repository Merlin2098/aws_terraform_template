# Install Terraform on Windows

Use this guide when you need a clear Windows setup path for:

* Terraform installation using the official HashiCorp binary
* Manual `PATH` configuration
* Corporate/restricted environment compatibility
* Initial Terraform + AWS CLI validation workflow

This guide intentionally avoids package managers such as Chocolatey to keep the

installation process explicit, portable, and reproducible.

---

# 1. Download Terraform From the Official HashiCorp Website

Open the official Terraform download page:

[Terraform Downloads](https://developer.hashicorp.com/terraform/downloads?utm_source=chatgpt.com)

Download:

* Windows AMD64 ZIP package

Example:

<pre class="overflow-visible! px-0!" data-start="1419" data-end="1464"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>terraform_1.x.x_windows_amd64.zip</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# 2. Extract Terraform

Create a local tools directory.

Recommended example:

<pre class="overflow-visible! px-0!" data-start="1550" data-end="1590"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>C:\approved-tools\terraform\</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

Extract the ZIP contents into that folder.

Expected structure:

<pre class="overflow-visible! px-0!" data-start="1657" data-end="1710"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>C:\approved-tools\terraform\terraform.exe</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# 3. Verify Terraform Binary Directly

Open PowerShell and run:

<pre class="overflow-visible! px-0!" data-start="1782" data-end="1849"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ10">C:</span><span>\</span><span class="ͼ11">approved-tools</span><span>\</span><span class="ͼ11">terraform</span><span>\</span><span class="ͼ11">terraform</span><span>.</span><span class="ͼ11">exe</span><span></span><span class="ͼ11">version</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

Expected output:

<pre class="overflow-visible! px-0!" data-start="1869" data-end="1897"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>Terraform v1.x.x</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# 4. Add Terraform to PATH (Current Session Only)

Use this when you want temporary access without modifying the machine

configuration.

<pre class="overflow-visible! px-0!" data-start="2041" data-end="2151"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">$env:Path</span><span></span><span class="ͼv">=</span><span></span><span class="ͼz">"C:\approved-tools\terraform;</span><span class="ͼ11">$env:Path</span><span class="ͼz">"</span><br/><br/><span class="ͼ11">terraform</span><span></span><span class="ͼ11">version</span><br/><span class="ͼ10">Get-Command</span><span></span><span class="ͼ11">terraform</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

This only affects the current PowerShell session.

---

# 5. Add Terraform to User PATH Permanently (No Admin Rights)

Use this when administrator rights are unavailable.

<pre class="overflow-visible! px-0!" data-start="2325" data-end="2575"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">$userPath</span><span></span><span class="ͼv">=</span><span> [</span><span class="ͼ11">System</span><span>.</span><span class="ͼ11">Environment</span><span>]</span><span class="ͼv">::</span><span class="ͼ11">GetEnvironmentVariable</span><span>(</span><span class="ͼz">"Path"</span><span>, </span><span class="ͼz">"User"</span><span>)</span><br/><br/><span>[</span><span class="ͼ11">System</span><span>.</span><span class="ͼ11">Environment</span><span>]</span><span class="ͼv">::</span><span class="ͼ11">SetEnvironmentVariable</span><span>(</span><br/><span></span><span class="ͼz">"Path"</span><span>,</span><br/><span></span><span class="ͼz">"</span><span class="ͼ11">$userPath</span><span class="ͼz">;C:\approved-tools\terraform"</span><span>,</span><br/><span></span><span class="ͼz">"User"</span><br/><span>)</span><br/><br/><span class="ͼ10">Write-Host</span><span></span><span class="ͼz">"Terraform added to user PATH"</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

Close and reopen PowerShell, then verify:

<pre class="overflow-visible! px-0!" data-start="2620" data-end="2677"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">terraform</span><span></span><span class="ͼ11">version</span><br/><span class="ͼ10">Get-Command</span><span></span><span class="ͼ11">terraform</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

This persists Terraform access for the current user profile only.

---

# 6. Add Terraform to System PATH Permanently (Admin)

Use this when you manage the machine and want Terraform available system-wide.

Open PowerShell as Administrator:

<pre class="overflow-visible! px-0!" data-start="2921" data-end="3194"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">$terraformPath</span><span></span><span class="ͼv">=</span><span></span><span class="ͼz">"C:\approved-tools\terraform"</span><br/><br/><span>[</span><span class="ͼ11">System</span><span>.</span><span class="ͼ11">Environment</span><span>]</span><span class="ͼv">::</span><span class="ͼ11">SetEnvironmentVariable</span><span>(</span><br/><span></span><span class="ͼz">"Path"</span><span>,</span><br/><span>    [</span><span class="ͼ11">System</span><span>.</span><span class="ͼ11">Environment</span><span>]</span><span class="ͼv">::</span><span class="ͼ11">GetEnvironmentVariable</span><span>(</span><span class="ͼz">"Path"</span><span>, </span><span class="ͼz">"Machine"</span><span>) </span><span class="ͼv">+</span><span></span><span class="ͼz">";</span><span class="ͼ11">$terraformPath</span><span class="ͼz">"</span><span>,</span><br/><span></span><span class="ͼz">"Machine"</span><br/><span>)</span><br/><br/><span class="ͼ10">Write-Host</span><span></span><span class="ͼz">"Terraform added to system PATH"</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

Close and reopen PowerShell, then verify:

<pre class="overflow-visible! px-0!" data-start="3239" data-end="3296"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">terraform</span><span></span><span class="ͼ11">version</span><br/><span class="ͼ10">Get-Command</span><span></span><span class="ͼ11">terraform</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# 7. Install AWS CLI

Terraform commonly interacts with AWS services, so AWS CLI should also be

installed and validated.

Download:

[AWS CLI Installer](https://aws.amazon.com/cli/?utm_source=chatgpt.com)

Verify installation:

<pre class="overflow-visible! px-0!" data-start="3531" data-end="3578"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">aws</span><span></span><span class="ͼv">--</span><span class="ͼ11">version</span><br/><span class="ͼ10">Get-Command</span><span></span><span class="ͼ11">aws</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# 8. Configure AWS Credentials

## Option A: Standard AWS Configure

Run:

<pre class="overflow-visible! px-0!" data-start="3660" data-end="3691"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">aws</span><span></span><span class="ͼ11">configure</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

Provide:

<pre class="overflow-visible! px-0!" data-start="3703" data-end="3791"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>AWS Access Key ID</span><br/><span>AWS Secret Access Key</span><br/><span>Default region</span><br/><span>Default output format</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

This creates:

<pre class="overflow-visible! px-0!" data-start="3808" data-end="3880"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>C:\Users\<USER>\.aws\credentials</span><br/><span>C:\Users\<USER>\.aws\config</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

## Option B: Environment Variables (.env.credentials)

Example:

<pre class="overflow-visible! px-0!" data-start="3952" data-end="4050"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>AWS_ACCESS_KEY_ID=XXXXXXXX</span><br/><span>AWS_SECRET_ACCESS_KEY=XXXXXXXX</span><br/><span>AWS_DEFAULT_REGION=us-east-1</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

Load credentials into the current PowerShell session:

<pre class="overflow-visible! px-0!" data-start="4107" data-end="4358"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ10">Get-Content</span><span></span><span class="ͼ11">infra</span><span>\</span><span class="ͼ11">env</span><span>\.</span><span class="ͼ11">env</span><span>.</span><span class="ͼ11">credentials</span><span></span><span class="ͼv">|</span><span></span><span class="ͼ10">ForEach-Object</span><span> {</span><br/><span></span><span class="ͼv">if</span><span> (</span><span class="ͼ10">$_</span><span></span><span class="ͼv">-match</span><span></span><span class="ͼz">"^\s*#"</span><span></span><span class="ͼv">-or</span><span></span><span class="ͼ10">$_</span><span></span><span class="ͼv">-match</span><span></span><span class="ͼz">"^\s*</span><span class="ͼ15">$</span><span class="ͼz">"</span><span>) { </span><span class="ͼv">return</span><span> }</span><br/><br/><span></span><span class="ͼ11">$name</span><span>, </span><span class="ͼ11">$value</span><span></span><span class="ͼv">=</span><span></span><span class="ͼ10">$_</span><span></span><span class="ͼv">-split</span><span></span><span class="ͼz">"="</span><span>, </span><span class="ͼy">2</span><br/><span>  [</span><span class="ͼ11">Environment</span><span>]</span><span class="ͼv">::</span><span class="ͼ11">SetEnvironmentVariable</span><span>(</span><span class="ͼ11">$name</span><span>.</span><span class="ͼ11">Trim</span><span>(), </span><span class="ͼ11">$value</span><span>.</span><span class="ͼ11">Trim</span><span>(), </span><span class="ͼz">"Process"</span><span>)</span><br/><span>}</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

Validate credentials:

<pre class="overflow-visible! px-0!" data-start="4383" data-end="4428"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">aws</span><span></span><span class="ͼ11">sts</span><span></span><span class="ͼ11">get-caller-identity</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# 9. Initial Terraform Validation Workflow

Recommended validation flow before any deployment.

---

## Terraform Init

<pre class="overflow-visible! px-0!" data-start="4555" data-end="4600"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">terraform</span><span></span><span class="ͼv">-</span><span class="ͼ10">chdir</span><span class="ͼv">=</span><span class="ͼ11">infra</span><span></span><span class="ͼ11">init</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

## Terraform Format Validation

<pre class="overflow-visible! px-0!" data-start="4639" data-end="4690"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">terraform</span><span></span><span class="ͼv">-</span><span class="ͼ10">chdir</span><span class="ͼv">=</span><span class="ͼ11">infra</span><span></span><span class="ͼ11">fmt</span><span></span><span class="ͼv">-</span><span class="ͼ11">check</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

## Terraform Validate

<pre class="overflow-visible! px-0!" data-start="4720" data-end="4769"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">terraform</span><span></span><span class="ͼv">-</span><span class="ͼ10">chdir</span><span class="ͼv">=</span><span class="ͼ11">infra</span><span></span><span class="ͼ11">validate</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

## Terraform Plan

<pre class="overflow-visible! px-0!" data-start="4795" data-end="4854"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">terraform</span><span></span><span class="ͼv">-</span><span class="ͼ10">chdir</span><span class="ͼv">=</span><span class="ͼ11">infra</span><span></span><span class="ͼ11">plan</span><span></span><span class="ͼv">-</span><span class="ͼ11">out</span><span class="ͼv">=</span><span class="ͼz">"tfplan"</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

## Terraform Apply

<pre class="overflow-visible! px-0!" data-start="4881" data-end="4936"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">terraform</span><span></span><span class="ͼv">-</span><span class="ͼ10">chdir</span><span class="ͼv">=</span><span class="ͼ11">infra</span><span></span><span class="ͼ11">apply</span><span></span><span class="ͼz">"tfplan"</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

## Terraform Outputs

<pre class="overflow-visible! px-0!" data-start="4965" data-end="5012"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">terraform</span><span></span><span class="ͼv">-</span><span class="ͼ10">chdir</span><span class="ͼv">=</span><span class="ͼ11">infra</span><span></span><span class="ͼ11">output</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

JSON format:

<pre class="overflow-visible! px-0!" data-start="5028" data-end="5081"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">terraform</span><span></span><span class="ͼv">-</span><span class="ͼ10">chdir</span><span class="ͼv">=</span><span class="ͼ11">infra</span><span></span><span class="ͼ11">output</span><span></span><span class="ͼv">-</span><span class="ͼ11">json</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# 10. Recommended Corporate Practices

For restricted corporate environments:

* Prefer official portable binaries
* Avoid package managers when possible
* Keep Terraform version explicit
* Use local user-scoped PATH configuration
* Store helper scripts under:

<pre class="overflow-visible! px-0!" data-start="5350" data-end="5389"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>tests/aws/</span><br/><span>scripts/windows/</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

* Avoid hardcoding credentials inside `.tfvars`
* Prefer `.env.credentials` or AWS profiles
* Validate IAM permissions before deployment

Recommended validation checks before `apply`:

<pre class="overflow-visible! px-0!" data-start="5576" data-end="5685"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">terraform</span><span></span><span class="ͼ11">version</span><br/><span class="ͼ11">aws</span><span></span><span class="ͼv">--</span><span class="ͼ11">version</span><br/><span class="ͼ11">aws</span><span></span><span class="ͼ11">sts</span><span></span><span class="ͼ11">get-caller-identity</span><br/><span class="ͼ11">terraform</span><span></span><span class="ͼv">-</span><span class="ͼ10">chdir</span><span class="ͼv">=</span><span class="ͼ11">infra</span><span></span><span class="ͼ11">validate</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# 11. Quick Verification Commands

<pre class="overflow-visible! px-0!" data-start="5727" data-end="5904"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ11">terraform</span><span></span><span class="ͼ11">version</span><br/><span class="ͼ11">terraform</span><span></span><span class="ͼv">-</span><span class="ͼ10">help</span><br/><span class="ͼ10">Get-Command</span><span></span><span class="ͼ11">terraform</span><br/><br/><span class="ͼ11">aws</span><span></span><span class="ͼv">--</span><span class="ͼ11">version</span><br/><span class="ͼ11">aws</span><span></span><span class="ͼ11">sts</span><span></span><span class="ͼ11">get-caller-identity</span><br/><br/><span class="ͼ11">terraform</span><span></span><span class="ͼv">-</span><span class="ͼ10">chdir</span><span class="ͼv">=</span><span class="ͼ11">infra</span><span></span><span class="ͼ11">init</span><br/><span class="ͼ11">terraform</span><span></span><span class="ͼv">-</span><span class="ͼ10">chdir</span><span class="ͼv">=</span><span class="ͼ11">infra</span><span></span><span class="ͼ11">validate</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# 12. Recommended Tooling

Recommended tooling for a reproducible AI-assisted Terraform workflow:

* Terraform
* AWS CLI
* GNU Make
* Python 3.12+
* uv
* Git
* VSCode
* Claude Code
* Codex
* Ruff
* Pytest
* pre-commit
