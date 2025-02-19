import puppeteer from 'puppeteer';
import * as cheerio from 'cheerio';
import * as fs from 'fs';

// Move interfaces to top-level for reuse
interface Opportunity {
    programName: string;
    service: string;
    city: string;
    state: string;
    duration: string;
    employerPOC: string;
    pocEmail: string;
    cost: string;
    deliveryMethod: string;
    closestInstallation: string;
    opportunityLocationsByState: string;
    targetMOCs: string;
    otherEligibilityFactors: string;
    otherPrerequisite: string;
    jobsDescription: string;
    summaryDescription: string;
    jobFamily: string;
    mouOrganization: string;
}

interface Location {
    company: string;
    opportunities: Opportunity[];
}

// Helper function to extract locations from a cheerio instance.
// When clickable is true and page is available, control cell clicks are performed.
async function extractLocations($: cheerio.Root, page?: puppeteer.Page, clickable: boolean = false): Promise<Location[]> {
    const locations: Location[] = [];
    const companyRows = $('tr.dtrg-group.dtrg-start.dtrg-level-0').toArray();

    for (let i = 0; i < companyRows.length; i++) {
        const companyRow = companyRows[i];
        const companyName = $(companyRow).find('td').first().text().trim();
        const opportunities: Opportunity[] = [];
        
        if (clickable && page) {
            const controlCellSelector = 'td.control.sorting_1';
            try {
                await page.evaluate((selector, idx) => {
                    const cells = document.querySelectorAll(selector);
                    if (cells && cells[idx]) {
                        (cells[idx] as HTMLElement).click();
                    }
                }, controlCellSelector, i);
                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
                console.error("Error clicking control cell:", error);
            }
        }
        let currentRow = $(companyRow).next();
        while (currentRow.length > 0 && !currentRow.hasClass('dtrg-group')) {
            if (!currentRow.hasClass('child')) {
                const tds = currentRow.find('td');
                if (tds.length >= 12) {
                    opportunities.push({
                        programName: $(tds[1]).text().trim(),
                        service: $(tds[2]).text().trim(),
                        city: $(tds[3]).text().trim(),
                        state: $(tds[4]).text().trim(),
                        duration: $(tds[5]).text().trim(),
                        employerPOC: $(tds[6]).text().trim(),
                        pocEmail: $(tds[7]).text().trim(),
                        cost: $(tds[8]).text().trim(),
                        deliveryMethod: $(tds[11]).text().trim(),
                        closestInstallation: '',
                        opportunityLocationsByState: '',
                        targetMOCs: '',
                        otherEligibilityFactors: '',
                        otherPrerequisite: '',
                        jobsDescription: '',
                        summaryDescription: '',
                        jobFamily: '',
                        mouOrganization: '',
                    });
                }
            } else if (currentRow.hasClass('child') && opportunities.length > 0) {
                const detailsList = currentRow.find('ul.dtr-details > li');
                const opportunity = opportunities[opportunities.length - 1];
                detailsList.each((i, detail) => {
                    const title = $(detail).find('span.dtr-title').text().trim();
                    const data = $(detail).find('span.dtr-data').text().trim();
                    switch (title) {
                        case 'Closest Installation':
                            opportunity.closestInstallation = data;
                            break;
                        case 'Opportunity Locations by State':
                            opportunity.opportunityLocationsByState = data;
                            break;
                        case 'Target MOCs':
                            opportunity.targetMOCs = data;
                            break;
                        case 'Other Eligibility Factors':
                            opportunity.otherEligibilityFactors = data;
                            break;
                        case 'Other/Prerequisite':
                            opportunity.otherPrerequisite = data;
                            break;
                        case 'Jobs Description':
                            opportunity.jobsDescription = data;
                            break;
                        case 'Summary Description':
                            opportunity.summaryDescription = data;
                            break;
                        case 'Job Family':
                            opportunity.jobFamily = data;
                            break;
                        case 'MOU Organization':
                            opportunity.mouOrganization = data;
                            break;
                    }
                });
            }
            currentRow = currentRow.next();
        }
        locations.push({ company: companyName, opportunities });
    }
    return locations;
}

async function scrapeSkillbridgeLocationsPuppeteer() {
    const browser = await puppeteer.launch({ headless: false }); // or false if you want to see the browser
    const page = await browser.newPage();

    try {
        await page.goto('https://skillbridge.osd.mil/locations.htm');

        // **Search Form Submission**
        // 1. Identify the search input field (using the provided HTML)
        const searchInputFieldSelector = '#keywords';
        await page.waitForSelector(searchInputFieldSelector);

        await new Promise(resolve => setTimeout(resolve, 500));

        // 2. Type "*" into the search input
        await page.type(searchInputFieldSelector, '*');

        await new Promise(resolve => setTimeout(resolve, 500));

        // 3. Identify the search submit button (using the provided HTML)
        const searchButtonSelector = '#loc-search-btn';
        await page.waitForSelector(searchButtonSelector);

        // 4. Click the search button
        await page.click(searchButtonSelector);

        // 5. Wait for a short period to allow dynamic filtering (adjust timeout if needed)
        await new Promise(resolve => setTimeout(resolve, 2500)); // Increased wait to 2.5 seconds to be safe

        // **Wait for the results to load and be visible**
        await page.waitForSelector('#results-container', { visible: true, timeout: 10000 });

        // Use helper function for initial extraction with clickable = true
        const resultsHTML = await page.$eval('#results-container', container => container.outerHTML);
        let $ = cheerio.load(resultsHTML);
        let locations = await extractLocations($, page, true);
        fs.writeFileSync('skillbridge_locations_search_button_puppeteer.json', JSON.stringify(locations, null, 2));
        console.log('Data scraped using Puppeteer with search "*" and button click, saved to skillbridge_locations_search_button_puppeteer.json');

        // **Pagination Handling (Basic - Needs more robust logic for "Next" button)**
        let pageNumber = 1;
        while (true) {
            // Check the info element to see if we're on the last page
            const infoElement = await page.$('#location-table_info');
            if (!infoElement) {
                break; // If the info element doesn't exist, stop pagination
            }
            const infoText = await page.evaluate(element => element.textContent, infoElement);
            if (!infoText) {
                break; // If the info text is null, stop pagination
            }
            // Example: "Showing 161 to 170 of 170 entries"
            const matches = infoText.match(/Showing (\d+) to (\d+) of (\d+) entries/);
            if (!matches) {
                break; // If the info text doesn't match the expected format, stop pagination
            }

            const [, start, end, total] = matches.map(Number);
            if (end === total) {
                break; // If the "to" number is equal to the total, we're on the last page
            }

            const nextButton = await page.$('#location-table_next');
            if (!nextButton) {
                break;
            }

            pageNumber++;
            console.log(`Navigating to page ${pageNumber}...`);
            console.log(`Entries on page: ${start} to ${end} of ${total}`);
            try {
                await nextButton.click(); // Click "Next"
                await new Promise(resolve => setTimeout(resolve, 2500)); // Wait for 2.5 seconds after clicking
            } catch (e) {
                console.error("Navigation timed out or failed:", e);
                break; // Stop pagination if navigation fails
            }

            // Extract HTML and use helper without clicking (clickable = false)
            const nextPageResultsHTML = await page.$eval('#results-container', container => container.outerHTML);
            $ = cheerio.load(nextPageResultsHTML);
            const newLocations = await extractLocations($, undefined, false);
            locations = locations.concat(newLocations);
            console.log(`Data from page ${pageNumber} appended.`);
        }

        fs.writeFileSync('skillbridge_locations_search_button_all_pages_puppeteer.json', JSON.stringify(locations, null, 2));
        console.log('Data scraped from all pages with search "*" and button click, saved to skillbridge_locations_search_button_all_pages_puppeteer.json');

    } catch (error) {
        console.error('Error scraping data with Puppeteer:', error);
    } finally {
        await browser.close();
    }
}

scrapeSkillbridgeLocationsPuppeteer();