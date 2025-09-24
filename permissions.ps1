# Complete Exchange Online SMTP Setup Script
# Part 1: Azure AD Application Permissions

# Install required modules for current user (no admin required)
Install-Module Microsoft.Graph.Beta.Applications -Force -AllowClobber -Scope CurrentUser
Install-Module -Name ExchangeOnlineManagement -Force -AllowClobber -Scope CurrentUser

# Import modules explicitly
Import-Module Microsoft.Graph.Beta.Applications
Import-Module ExchangeOnlineManagement

# Connect to Microsoft Graph
Connect-MgGraph -Scopes AppRoleAssignment.ReadWrite.All,Application.Read.All

# Set your app name
$myappName = 'HPCEmailBlast'

Write-Host "Setting up Azure AD permissions for: $myappName" -ForegroundColor Green

# Get service principals
$myappServicePrincipal = Get-MgBetaServicePrincipal -Filter "displayName eq '$myappName'"
$exoServicePrincipal = Get-MgBetaServicePrincipal -Filter "AppId eq '00000002-0000-0ff1-ce00-000000000000'" 
$exoPermission = $exoServicePrincipal.AppRoles | Where-Object {$_.DisplayName -eq "Manage Exchange As Application"}

if ($myappServicePrincipal -eq $null) {
    Write-Error "App '$myappName' not found. Please check the app name."
    exit 1
}

# Assign Azure AD permissions
New-MgBetaServicePrincipalAppRoleAssignment -ServicePrincipalId $myappServicePrincipal.Id -BodyParameter @{
    "PrincipalId" = $myappServicePrincipal.Id
    "ResourceId" = $exoServicePrincipal.Id
    "AppRoleId" = $exoPermission.Id
}

Write-Host "Azure AD permissions assigned successfully!" -ForegroundColor Green

# Part 2: Exchange Online Service Principal Registration

Write-Host "Connecting to Exchange Online..." -ForegroundColor Yellow
Write-Host "You will be prompted to sign in with your admin account." -ForegroundColor Yellow

# Connect to Exchange Online (you'll be prompted for credentials)
Connect-ExchangeOnline

Write-Host "Registering service principal in Exchange Online..." -ForegroundColor Green

# Register service principal in Exchange Online
New-ServicePrincipal -AppId $myappServicePrincipal.AppId -ObjectId $myappServicePrincipal.Id

Write-Host "Service principal registered successfully!" -ForegroundColor Green

# Display app information
Write-Host "\n=== App Information ===" -ForegroundColor Cyan
Write-Host "App Name: $($myappServicePrincipal.DisplayName)"
Write-Host "App ID (Client ID): $($myappServicePrincipal.AppId)"
Write-Host "Object ID: $($myappServicePrincipal.Id)"

# Prompt for mailbox permissions
Write-Host "\n=== Mailbox Permissions Setup ===" -ForegroundColor Cyan
$senderEmail = Read-Host "Enter the sender email address that will send emails (e.g., sender@yourdomain.com)"

if ($senderEmail -ne "") {
    Write-Host "Granting mailbox permissions..." -ForegroundColor Green
    
    # Grant FullAccess permission
    Add-MailboxPermission -Identity $senderEmail -User $myappServicePrincipal.Id -AccessRights FullAccess
    
    # Grant SendAs permission
    Add-RecipientPermission -Identity $senderEmail -Trustee $myappServicePrincipal.Id -AccessRights SendAs -Confirm:$false
    
    Write-Host "Mailbox permissions granted for: $senderEmail" -ForegroundColor Green
} else {
    Write-Host "Skipping mailbox permissions. You can set them later with:" -ForegroundColor Yellow
    Write-Host "Add-MailboxPermission -Identity 'email@domain.com' -User '$($myappServicePrincipal.Id)' -AccessRights FullAccess"
    Write-Host "Add-RecipientPermission -Identity 'email@domain.com' -Trustee '$($myappServicePrincipal.Id)' -AccessRights SendAs"
}

Write-Host "\n=== Setup Complete! ===" -ForegroundColor Green
Write-Host "Your app is now configured for SMTP authentication." -ForegroundColor Green
Write-Host "OAuth scope to use: https://outlook.office365.com/.default" -ForegroundColor Cyan

# Disconnect
Disconnect-MgGraph
Disconnect-ExchangeOnline -Confirm:$false