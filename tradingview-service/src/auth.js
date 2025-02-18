const { Builder, By, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const { ServiceBuilder } = require('selenium-webdriver/chrome');
const chromedriver = require('chromedriver');

async function handleCaptchaLogin(username, password) {
    let driver;
    console.log('Starting CAPTCHA login process with Selenium...');
    
    try {
        console.log('Setting up Chrome options...');
        
        // Set up Chrome options
        const options = new chrome.Options();
        options.addArguments('--no-sandbox');
        options.addArguments('--disable-dev-shm-usage');
        options.addArguments('--start-maximized');
        
        const service = new ServiceBuilder(chromedriver.path);

        console.log('Creating Chrome driver...');
        driver = await new Builder()
            .forBrowser('chrome')
            .setChromeOptions(options)
            .setChromeService(service)
            .build();

        console.log('Navigating to TradingView sign in...');
        await driver.get('https://www.tradingview.com/accounts/signin/');
        
        // Wait for page load
        await driver.sleep(3000);

        // Handle cookie preferences (if cookie consent dialog appears)
        try {
            const cookieAcceptButton = await driver.findElement(By.css('button[aria-label="Accept necessary cookies only"]'));
            await cookieAcceptButton.click();
            console.log('Accepted only necessary cookies');
            await driver.sleep(1000);
        } catch {
            console.log('No cookie consent dialog found or unable to click');
        }

        console.log('Looking for Email button...');
        const emailButton = await driver.wait(
            until.elementLocated(By.css('.emailButton-nKAw8Hvt')),
            15000
        );
        
        console.log('Clicking Email button...');
        await emailButton.click();
        
        // Wait for form transition
        await driver.sleep(3000);

        console.log('Filling in username...');
        const usernameInput = await driver.wait(
            until.elementLocated(By.id('id_username')),
            10000
        );
        await driver.executeScript("arguments[0].scrollIntoView(true);", usernameInput);
        await driver.sleep(500);
        await usernameInput.clear();
        await usernameInput.sendKeys(username);

        console.log('Filling in password...');
        const passwordInput = await driver.wait(
            until.elementLocated(By.id('id_password')),
            10000
        );
        await driver.executeScript("arguments[0].scrollIntoView(true);", passwordInput);
        await driver.sleep(500);
        await passwordInput.clear();
        await passwordInput.sendKeys(password);

        console.log('IMPORTANT: MANUAL INTERACTION REQUIRED');
        console.log('-----------------------------------');
        console.log('1. Complete the CAPTCHA in the browser');
        console.log('2. Fully log in to TradingView');
        console.log('3. DO NOT CLOSE the browser');
        console.log('4. After COMPLETE login, this script will continue');
        console.log('-----------------------------------');

        console.log('Clicking sign in button...');
        const signInButton = await driver.wait(
            until.elementLocated(By.css('.submitButton-LQwxK8Bm')),
            10000
        );
        await driver.sleep(1000);
        await driver.executeScript("arguments[0].scrollIntoView(true);", signInButton);
        await driver.sleep(500);
        await signInButton.click();

        // Wait for manual login completion
        const startTime = Date.now();
        const maxWaitTime = 300000; // 5 minutes

        while ((Date.now() - startTime) < maxWaitTime) {
            const currentUrl = await driver.getCurrentUrl();
            console.log('Current URL:', currentUrl);

            // Explicitly wait until we are NOT on the signin page
            if (!currentUrl.includes('/accounts/signin/') && currentUrl.startsWith('https://www.tradingview.com/')) {
                console.log('Successfully redirected from signin page.');
                
                // Wait a bit more to ensure cookies are set
                await driver.sleep(3000);

                // Get cookies after redirect
                const cookies = await driver.manage().getCookies();
                console.log('Cookies after redirect:', cookies.length);
                
                const sessionidCookie = cookies.find(cookie => cookie.name === 'sessionid');
                const sessionidSignCookie = cookies.find(cookie => cookie.name === 'sessionid_sign');

                if (sessionidCookie && sessionidSignCookie) {
                    console.log('Found valid session and signature cookies!');
                    return {
                        session: sessionidCookie.value,
                        signature: sessionidSignCookie.value
                    };
                }
            }

            // Short wait before next check
            await driver.sleep(2000);
        }

        throw new Error('Login timeout: Could not complete login process');

    } catch (error) {
        console.error('CAPTCHA login error:', error);
        throw error;
    } finally {
        if (driver) {
            console.log('Closing browser...');
            try {
                await driver.quit();
            } catch (e) {
                console.error('Error closing browser:', e);
            }
        }
    }
}

module.exports = { handleCaptchaLogin };
