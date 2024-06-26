const { getSPF, getDMARC, getDKIM } = require('./dnsUtils');

module.exports = async (req, res) => {
  const { domain, selector } = req.query;
  if (!domain) {
    return res.status(400).json({ error: "Domain is required" });
  }

  try {
    const spf = await getSPF(domain);
    const dmarc = await getDMARC(domain);
    const dkim = await getDKIM(domain, selector || 'default');

    res.json({ SPF: spf, DMARC: dmarc, DKIM: dkim });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
