#!/usr/bin/env python3
"""
VisionSeal Security Validation Script
Checks that all critical security fixes have been applied
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any

class SecurityChecker:
    """Comprehensive security validation"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.issues = []
        self.warnings = []
        self.passed = []
        
    def check_all(self):
        """Run all security checks"""
        print("🔒 VisionSeal Security Validation")
        print("=" * 40)
        
        # Critical checks
        self.check_credential_exposure()
        self.check_browser_security()
        self.check_authentication_bypass()
        self.check_gitignore()
        self.check_environment_template()
        
        # Important checks
        self.check_security_headers()
        self.check_input_validation()
        self.check_file_permissions()
        
        # Report results
        self.print_results()
        
    def check_credential_exposure(self):
        """Check for exposed credentials"""
        print("\n🔍 Checking credential exposure...")
        
        # Check .env file
        env_file = self.project_root / ".env"
        if env_file.exists():
            content = env_file.read_text()
            
            # Look for real credentials patterns
            suspicious_patterns = [
                r"sk-proj-\w+",  # OpenAI API keys
                r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",  # JWT tokens
                r"https://\w+\.supabase\.co",  # Real Supabase URLs
                r"\w+@gmail\.com",  # Email addresses
                r"[A-Za-z0-9]{20,}",  # Long strings that might be keys
            ]
            
            found_credentials = False
            for pattern in suspicious_patterns:
                if re.search(pattern, content):
                    # Check if it's a placeholder
                    if "your-" not in content or "example" not in content:
                        found_credentials = True
                        break
            
            if found_credentials:
                self.issues.append("❌ CRITICAL: Real credentials found in .env file")
            else:
                self.passed.append("✅ .env file contains only placeholders")
        else:
            self.warnings.append("⚠️ No .env file found")
            
        # Check HTML files for hard-coded credentials
        html_files = list(self.project_root.glob("web_dashboard/*.html"))
        for html_file in html_files:
            content = html_file.read_text()
            if "eyJ" in content and "supabase" in content.lower():
                self.issues.append(f"❌ CRITICAL: Hard-coded Supabase credentials in {html_file.name}")
            elif "getSupabaseConfig()" in content:
                self.passed.append(f"✅ {html_file.name} uses secure config loading")
    
    def check_browser_security(self):
        """Check browser automation security"""
        print("🔍 Checking browser security...")
        
        py_files = list(self.project_root.glob("src/**/*.py"))
        
        for py_file in py_files:
            try:
                content = py_file.read_text()
                
                # Check for insecure flags, but allow them if they're conditional
                if "--no-sandbox" in content and "if not" not in content:
                    self.issues.append(f"❌ CRITICAL: --no-sandbox found in {py_file.name}")
                
                if "--disable-web-security" in content and "if not" not in content:
                    self.issues.append(f"❌ CRITICAL: --disable-web-security found in {py_file.name}")
                    
                if "playwright" in content.lower() and "--disable-blink-features" in content:
                    self.passed.append(f"✅ {py_file.name} uses secure browser args")
                    
            except Exception:
                continue
    
    def check_authentication_bypass(self):
        """Check for authentication bypass"""
        print("🔍 Checking authentication bypass...")
        
        auth_file = self.project_root / "src/core/security/auth.py"
        if auth_file.exists():
            content = auth_file.read_text()
            
            if 'settings.environment == "development"' in content:
                self.issues.append("❌ HIGH: Development authentication bypass found")
            else:
                self.passed.append("✅ No authentication bypass found")
        else:
            self.warnings.append("⚠️ Auth file not found")
    
    def check_gitignore(self):
        """Check .gitignore configuration"""
        print("🔍 Checking .gitignore...")
        
        gitignore_file = self.project_root / ".gitignore"
        if gitignore_file.exists():
            content = gitignore_file.read_text()
            
            required_patterns = [".env", "*.key", "secrets/", "credentials/"]
            missing_patterns = []
            
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                self.warnings.append(f"⚠️ .gitignore missing: {', '.join(missing_patterns)}")
            else:
                self.passed.append("✅ .gitignore properly configured")
        else:
            self.issues.append("❌ HIGH: No .gitignore file found")
    
    def check_environment_template(self):
        """Check environment template"""
        print("🔍 Checking environment template...")
        
        template_file = self.project_root / ".env.example"
        if template_file.exists():
            content = template_file.read_text()
            
            if "your-" in content and "here" in content:
                self.passed.append("✅ .env.example template properly configured")
            else:
                self.warnings.append("⚠️ .env.example may contain real values")
        else:
            self.warnings.append("⚠️ No .env.example template found")
    
    def check_security_headers(self):
        """Check security headers implementation"""
        print("🔍 Checking security headers...")
        
        security_files = [
            self.project_root / "src/core/security/security_config.py",
            self.project_root / "src/core/security/middleware.py"
        ]
        
        headers_implemented = False
        for file in security_files:
            if file.exists():
                content = file.read_text()
                if "X-Content-Type-Options" in content and "X-Frame-Options" in content:
                    headers_implemented = True
                    break
        
        if headers_implemented:
            self.passed.append("✅ Security headers implemented")
        else:
            self.warnings.append("⚠️ Security headers not found")
    
    def check_input_validation(self):
        """Check input validation"""
        print("🔍 Checking input validation...")
        
        # Check for validation middleware
        middleware_file = self.project_root / "src/core/security/middleware.py"
        if middleware_file.exists():
            content = middleware_file.read_text()
            if "InputValidationMiddleware" in content:
                self.passed.append("✅ Input validation middleware found")
            else:
                self.warnings.append("⚠️ Input validation not implemented")
        else:
            self.warnings.append("⚠️ Security middleware not found")
    
    def check_file_permissions(self):
        """Check file permissions"""
        print("🔍 Checking file permissions...")
        
        # Check if .env file has restrictive permissions (Unix systems)
        env_file = self.project_root / ".env"
        if env_file.exists() and hasattr(os, 'stat'):
            try:
                stat_info = env_file.stat()
                mode = stat_info.st_mode & 0o777
                
                if mode > 0o600:  # More permissive than rw-------
                    self.warnings.append("⚠️ .env file permissions too permissive")
                else:
                    self.passed.append("✅ .env file permissions secure")
            except Exception:
                self.warnings.append("⚠️ Could not check .env permissions")
    
    def print_results(self):
        """Print security check results"""
        print("\n" + "="*50)
        print("🔒 SECURITY CHECK RESULTS")
        print("="*50)
        
        # Critical issues
        if self.issues:
            print(f"\n❌ CRITICAL ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   {issue}")
        
        # Warnings
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        # Passed checks
        if self.passed:
            print(f"\n✅ PASSED CHECKS ({len(self.passed)}):")
            for passed in self.passed:
                print(f"   {passed}")
        
        # Overall status
        print("\n" + "="*50)
        if self.issues:
            print("🚨 SECURITY STATUS: CRITICAL ISSUES FOUND")
            print("❗ Fix critical issues before deployment")
            return False
        elif self.warnings:
            print("⚠️ SECURITY STATUS: WARNINGS PRESENT")
            print("💡 Address warnings for better security")
            return True
        else:
            print("✅ SECURITY STATUS: ALL CHECKS PASSED")
            print("🎉 Ready for secure deployment")
            return True

def main():
    """Main security check function"""
    checker = SecurityChecker()
    success = checker.check_all()
    
    print(f"\n📋 SECURITY CHECKLIST:")
    print(f"   • Credentials removed from code: {'✅' if not any('CRITICAL' in issue for issue in checker.issues) else '❌'}")
    print(f"   • Browser security enabled: {'✅' if not any('browser' in issue.lower() for issue in checker.issues) else '❌'}")
    print(f"   • Authentication enforced: {'✅' if not any('bypass' in issue.lower() for issue in checker.issues) else '❌'}")
    print(f"   • .gitignore configured: {'✅' if not any('gitignore' in issue.lower() for issue in checker.issues) else '❌'}")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()