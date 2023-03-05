"""Deploy Enzyme protcol v4.

Based on https://github.com/enzymefinance/protocol/blob/v4/packages/protocol/tests/release/e2e/FundManagementWalkthrough.test.ts
"""
from eth_typing import HexAddress
from web3 import Web3
from web3.contract import Contract

from eth_defi.enzyme.deployment import EnzymeDeployment, RateAsset


def test_deploy_enzyme(
        web3: Web3,
        deployer: HexAddress,
        fund_owner: HexAddress,
        fund_client: HexAddress,
        weth: Contract,
        mln: Contract,
        usdc: Contract,
        usdc_usd_mock_chainlink_aggregator: Contract,
):
    """Deploy Enzyme protocol, single USDC nominated vault and buy in."""

    deployment = EnzymeDeployment.deploy_core(
        web3,
        deployer,
        mln,
        weth,
    )

    # Create a vault for user 1
    # where we nominate everything in USDC
    deployment.add_primitive(
        usdc,
        usdc_usd_mock_chainlink_aggregator,
        RateAsset.USD,
    )

    comptroller, vault = deployment.create_new_vault(
        fund_owner,
        usdc,
    )

    assert comptroller.functions.getDenominationAsset().call() == usdc.address
    assert vault.functions.getTrackedAssets().call() == [usdc.address]

    # User 2 buys into the vault
    # See Shares.sol
    #
    # Buy shares for 500 USDC, receive min share
    usdc.functions.transfer(fund_client, 500 * 10 ** 6).transact({"from": deployer})
    usdc.functions.approve(comptroller.address, 500*10**6).transact({"from": fund_client})
    comptroller.functions.buyShares(500*10**6, 1).transact({"from": fund_client})

    # See user 2 received shares
    balance = vault.functions.balanceOf(fund_client).call()
    assert balance == 500*10**6
