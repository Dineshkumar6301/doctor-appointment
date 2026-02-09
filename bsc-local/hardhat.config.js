require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.19",
  networks: {
    hardhat: {
      forking: {
        url: "https://bsc-dataseed.binance.org/"
      }
    }
  }
};
