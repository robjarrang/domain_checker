const dns = require('dns');
const util = require('util');
const resolver = new dns.promises.Resolver();

// Function to get SPF records
const getSPF = async (domain) => {
  try {
    const records = await resolver.resolveTxt(domain);
    return records.filter(record => record.join("").startsWith("v=spf1"));
  } catch (error) {
    return `SPF record not found: ${error}`;
  }
};

// Function to get DMARC records
const getDMARC = async (domain) => {
  try {
    const records = await resolver.resolveTxt(`_dmarc.${domain}`);
    return records.filter(record => record.join("").startsWith("v=DMARC1"));
  } catch (error) {
    return `DMARC record not found: ${error}`;
  }
};

// Function to get DKIM records (assuming a selector 'default')
const getDKIM = async (domain, selector = 'default') => {
  try {
    const records = await resolver.resolveTxt(`${selector}._domainkey.${domain}`);
    return records;
  } catch (error) {
    return `DKIM record not found: ${error}`;
  }
};

module.exports = {
  getSPF,
  getDMARC,
  getDKIM
};
