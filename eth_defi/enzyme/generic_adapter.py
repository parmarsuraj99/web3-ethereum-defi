"""Enzyme generic adapter helpers."""
import logging
from typing import TypeAlias, Collection, Tuple

from eth_abi import encode
from eth_typing import HexAddress
from web3 import Web3
from web3.contract import Contract
from web3.types import TxParams

from eth_defi.enzyme.integration_manager import IntegrationManagerActionId

ExternalCall: TypeAlias = Tuple[Contract, bytes]

Asset: TypeAlias = Contract | HexAddress

Signer: TypeAlias = HexAddress


EXECUTE_CALLS_SELECTOR = Web3.keccak(b"executeCalls(address,bytes,bytes)")


logger = logging.getLogger(__name__)


def _addressify(asset: Contract | HexAddress):
    assert type(asset) == Contract or type(asset) == HexAddress, f"Got bad asset: {asset}"
    if isinstance(asset, Contract):
        return asset.address
    return asset


def _addressify_collection(assets: Collection[Contract | HexAddress]):
    return [_addressify(a) for a in asssets]


def encode_generic_adapter_execute_calls_args(
        incoming_assets: Collection[Asset],
        min_incoming_asset_amounts: Collection[int],
        spend_assets: Collection[Asset],
        spend_asset_amounts: Collection[int],
        external_calls: Collection[ExternalCall]
):
    """Encode arguments for a generic adapter call."""

#   const encodedExternalCallsData = encodeArgs(
#     ['address[]', 'bytes[]'],
#     [externalCallsData.contracts, externalCallsData.callsData],
#   );

    addresses = [t[0] for t in external_calls]
    datas = [t[1] for t in external_calls]

    encoded_external_calls_data = encode(
        ['address[]', 'bytes[]'],
        [addresses, datas]
    )

#   return encodeArgs(
#     ['address[]', 'uint256[]', 'address[]', 'uint256[]', 'bytes'],
#     [incomingAssets, minIncomingAssetAmounts, spendAssets, spendAssetAmounts, encodedExternalCallsData],
#   );

    all_args_encoded = encode(
        ['address[]', 'uint256[]', 'address[]', 'uint256[]', 'bytes'],
        [
            _addressify_collection(incoming_assets),
            min_incoming_asset_amounts,
            _addressify_collection(spend_assets),
            spend_asset_amounts,
            encoded_external_calls_data
        ],
    )

    return all_args_encoded


# export function callOnIntegrationArgs({
#   adapter,
#   selector,
#   encodedCallArgs,
# }: {
#   adapter: AddressLike;
#   selector: BytesLike;
#   encodedCallArgs: BytesLike;
# }) {
#   return encodeArgs(['address', 'bytes4', 'bytes'], [adapter, selector, encodedCallArgs]);
# }


def encode_call_on_integration_args(
    adapter: Contract,
    selector: bytes,
    encoded_call_args: bytes
):
    """No idea yet."""

    assert type(selector) == bytes
    assert type(encoded_call_args) == bytes
    assert len(selector) == 4
    assert len(encoded_call_args) > 0

    return encode(
        ['address', 'bytes4', 'bytes'],
        [
            _addressify(adapter),
            selector,
            encoded_call_args
        ]
    )


def execute_calls_for_generic_adapter(
        comptroller: Contract,
        external_calls: Collection[ExternalCall],
        generic_adapter: Contract,
        integration_manager: Contract,
        incoming_assets: Collection[Asset],
        min_incoming_asset_amounts: Collection[int],
        spend_assets: Collection[Asset],
        spend_asset_amounts: Collection[int],
) -> TxParams:
    """Create a vault buy/sell transaction using a generic adapter.

    :return:
        A transaction object prepared to be signed
    """

    logger.info(
        "execute_calls_for_generic_adapter(): %s %s %s %s %s %s %s %s",
        comptroller,
        external_calls,
        generic_adapter,
        integration_manager,
        incoming_assets,
        min_incoming_asset_amounts,
        spend_assets,
        spend_asset_amounts
    )

    # Sanity checks
    assert isinstance(comptroller, Contract)
    assert len(external_calls) > 0
    assert isinstance(generic_adapter, Contract)
    assert len(incoming_assets) > 0
    assert isinstance(integration_manager, Contract)
    assert len(min_incoming_asset_amounts) > 0
    assert len(spend_asset_amounts) > 0
    assert len(spend_assets) > 0

    execute_call_args = encode_generic_adapter_execute_calls_args(
        incoming_assets=incoming_assets,
        min_incoming_asset_amounts=min_incoming_asset_amounts,
        spend_assets=spend_assets,
        spend_asset_amounts=spend_asset_amounts,
        external_calls=external_calls,
    )

    call_args = encode_call_on_integration_args(
        generic_adapter,
        execute_call_args,
        EXECUTE_CALLS_SELECTOR,
    )

    # https://web3py.readthedocs.io/en/v5/contracts.html#contract-functions
    return comptroller.functions.callExtension(
        integration_manager,
        IntegrationManagerActionId.CallOnIntegration,
        call_args
    ).build_transaction()


# import type { AddressLike } from '@enzymefinance/ethers';
# import type { SignerWithAddress } from '@enzymefinance/hardhat';
# import type {
#   ComptrollerLib,
#   GenericAdapter,
#   GenericAdapterExternalCallsData,
#   IntegrationManager,
# } from '@enzymefinance/protocol';
# import {
#   callOnIntegrationArgs,
#   executeCallsSelector,
#   genericAdapterExecuteCallsArgs,
#   IntegrationManagerActionId,
# } from '@enzymefinance/protocol';
# import type { BigNumberish } from 'ethers';
#
# export async function genericAdapterExecuteCalls({
#   comptrollerProxy,
#   externalCallsData,
#   signer,
#   genericAdapter,
#   incomingAssets,
#   integrationManager,
#   minIncomingAssetAmounts,
#   spendAssetAmounts,
#   spendAssets,
# }: {
#   comptrollerProxy: ComptrollerLib;
#   externalCallsData: GenericAdapterExternalCallsData;
#   signer: SignerWithAddress;
#   genericAdapter: GenericAdapter;
#   incomingAssets: AddressLike[];
#   integrationManager: IntegrationManager;
#   minIncomingAssetAmounts: BigNumberish[];
#   spendAssetAmounts: BigNumberish[];
#   spendAssets: AddressLike[];
# }) {
#   const executeCallArgs = genericAdapterExecuteCallsArgs({
#     externalCallsData,
#     incomingAssets,
#     minIncomingAssetAmounts,
#     spendAssetAmounts,
#     spendAssets,
#   });
#
#   const callArgs = callOnIntegrationArgs({
#     adapter: genericAdapter,
#     encodedCallArgs: executeCallArgs,
#     selector: executeCallsSelector,
#   });
#
#   return comptrollerProxy
#     .connect(signer)
#     .callOnExtension(integrationManager, IntegrationManagerActionId.CallOnIntegration, callArgs);
# }
#
# import type { AddressLike } from '@enzymefinance/ethers';
# import type { BigNumberish, BytesLike } from 'ethers';
#
# import { encodeArgs } from '../encoding';
#
# export interface GenericAdapterExecuteCalls {
#   incomingAssets: AddressLike[];
#   minIncomingAssetAmounts: BigNumberish[];
#   spendAssets: AddressLike[];
#   spendAssetAmounts: BigNumberish[];
#   externalCallsData: GenericAdapterExternalCallsData;
# }
#
# export interface GenericAdapterExternalCallsData {
#   contracts: AddressLike[];
#   callsData: BytesLike[];
# }
#
# export function genericAdapterExecuteCallsArgs({
#   incomingAssets,
#   minIncomingAssetAmounts,
#   spendAssets,
#   spendAssetAmounts,
#   externalCallsData,
# }: GenericAdapterExecuteCalls) {
#   const encodedExternalCallsData = encodeArgs(
#     ['address[]', 'bytes[]'],
#     [externalCallsData.contracts, externalCallsData.callsData],
#   );
#
#   return encodeArgs(
#     ['address[]', 'uint256[]', 'address[]', 'uint256[]', 'bytes'],
#     [incomingAssets, minIncomingAssetAmounts, spendAssets, spendAssetAmounts, encodedExternalCallsData],
#   );
# }