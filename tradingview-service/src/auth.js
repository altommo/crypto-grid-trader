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

        console.log('Clicking sign in button...');
        const signInButton = await driver.wait(
            until.elementLocated(By.css('.submitButton-LQwxK8Bm')),
            10000
        );
        await driver.sleep(1000);
        await driver.executeScript("arguments[0].scrollIntoView(true);", signInButton);
        await driver.sleep(500);
        await signInButton.click();

        console.log('Please complete the CAPTCHA in the browser window if it appears...');
        console.log('Waiting for login completion...');

        // Wait for successful login
        let loginSuccessful = false;
        const startTime = Date.now();
        const maxWaitTime = 300000; // 5 minutes

        while (!loginSuccessful && (Date.now() - startTime) < maxWaitTime) {
            const currentUrl = await driver.getCurrentUrl();
            console.log('Current URL:', currentUrl);

            // Explicit checks for successful login
            const isMainPage = currentUrl.startsWith('https://www.tradingview.com/') && !currentUrl.includes('signin');
            const isNotSignInPage = !currentUrl.includes('/accounts/signin/');

            // Try to get cookies
            const cookies = await driver.manage().getCookies();
            console.log('Found cookies:', cookies.length);
            
            const sessionidCookie = cookies.find(cookie => cookie.name === 'sessionid');
            const sessionidSignCookie = cookies.find(cookie => cookie.name === 'sessionid_sign');

            // Detailed logging of login state
            console.log('Login State Check:', {
                isMainPage,
                isNotSignInPage,
                hasSessionidCookie: !!sessionidCookie,
                hasSessionidSignCookie: !!sessionidSignCookie
            });

            // Only consider login successful if we're on the main page or not on sign-in page
            if ((isMainPage || isNotSignInPage) && sessionidCookie && sessionidSignCookie) {
                loginSuccessful = true;
                console.log('Found required cookies and reached correct page!');
                return {
                    session: sessionidCookie.value,
                    signature: sessionidSignCookie.value
                };
            }

            await driver.sleep(2000); // Wait before next check
        }

        // If we're here, we timed out
        const finalCookies = await driver.manage().getCookies();
        const cookieNames = finalCookies.map(c => c.name).join(', ');
        throw new Error(`Timed out waiting for successful login. Available cookies: ${cookieNames}`);

    } catch (error) {
        console.error('CAPTCHA login error:', error);
        if (error.message.includes('ChromeDriver')) {
            console.error('ChromeDriver error. Make sure Chrome is installed and up to date.');
        }
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
