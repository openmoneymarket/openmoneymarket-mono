from .addresses import *
from .interfaces import *
from .proposals import *
from .utils.consts import *


class Governance(Addresses):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

        self._vote_duration = VarDB('vote_duration', db, int)
        # self._omm_vote_definition_criterion = VarDB('min_omm', db, int)
        self._boosted_omm_vote_definition_criterion = VarDB('min_boosted_omm', db, int)
        self._vote_definition_fee = VarDB('definition_fee', db, int)
        self._quorum = VarDB('quorum', db, int)

    def on_install(self, _addressProvider: Address) -> None:
        super().on_install(_addressProvider)

    def on_update(self) -> None:
        super().on_update()
        self._boosted_omm_vote_definition_criterion.set(EXA // 1000)

    @external(readonly=True)
    def name(self) -> str:
        return f"Omm {TAG}"

    @eventlog(indexed=2)
    def VoteCast(self, vote_name: str, vote: bool, voter: Address, stake: int, total_for: int, total_against: int):
        pass

    @eventlog(indexed=2)
    def ActionExecuted(self, vote_index: int, vote_status: str):
        pass

    @eventlog(indexed=2)
    def ProposalCreated(self, vote_index: int, name: str, proposer: Address):
        pass

    @only_owner
    @external
    def setReserveActiveStatus(self, _reserve: Address, _status: bool):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateIsActive(_reserve, _status)

    @only_owner
    @external
    def setReserveFreezeStatus(self, _reserve: Address, _status: bool):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateIsFreezed(_reserve, _status)

    @only_owner
    @external
    def setReserveConstants(self, _constants: List[Constant]):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.setReserveConstants(_constants)

    @only_owner
    @external
    def initializeReserve(self, _reserve: ReserveAttributes):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.addReserveData(_reserve)

    @only_owner
    @external
    def updateBaseLTVasCollateral(self, _reserve: Address, _baseLtv: int):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateBaseLTVasCollateral(_reserve, _baseLtv)

    @only_owner
    @external
    def updateLiquidationThreshold(self, _reserve: Address, _liquidationThreshold: int):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateLiquidationThreshold(_reserve, _liquidationThreshold)

    @only_owner
    @external
    def updateBorrowThreshold(self, _reserve: Address, _borrowThreshold: int):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateBorrowThreshold(_reserve, _borrowThreshold)

    @only_owner
    @external
    def updateLiquidationBonus(self, _reserve: Address, _liquidationBonus: int):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateLiquidationBonus(_reserve, _liquidationBonus)

    @only_owner
    @external
    def updateBorrowingEnabled(self, _reserve: Address, _borrowingEnabled: bool):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateBorrowingEnabled(_reserve, _borrowingEnabled)

    @only_owner
    @external
    def updateUsageAsCollateralEnabled(self, _reserve: Address, _usageAsCollateralEnabled: bool):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateUsageAsCollateralEnabled(_reserve, _usageAsCollateralEnabled)

    @only_owner
    @external
    def enableRewardClaim(self):
        rewards = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        rewards.enableRewardClaim()

    @only_owner
    @external
    def disableRewardClaim(self):
        rewards = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        rewards.disableRewardClaim()

    @only_owner
    @external
    def addPools(self, _assetConfigs: List[AssetConfig]):
        for assetConfig in _assetConfigs:
            self.addPool(assetConfig)

    @only_owner
    @external
    def addPool(self, _assetConfig: AssetConfig):
        _poolID = _assetConfig['poolID']
        if _poolID > 0:
            asset = _assetConfig['asset']
            stakedLP = self.create_interface_score(self._addresses[STAKED_LP], StakedLPInterface)
            stakedLP.addPool(_poolID, asset)

        rewards = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        rewards.configureAssetConfig(_assetConfig)

    @only_owner
    @external
    def removePool(self, _asset: Address):
        rewards = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        _poolID = rewards.getPoolIDByAsset(_asset)
        if _poolID > 0:
            stakedLP = self.create_interface_score(self._addresses[STAKED_LP], StakedLPInterface)
            stakedLP.removePool(_poolID)
        rewards.removeAssetConfig(_asset)

    @only_owner
    @external
    def transferOmmToDaoFund(self, _value: int):
        rewards = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        rewards.transferOmmToDaoFund(_value)

    @only_owner
    @external
    def transferOmmFromDaoFund(self, _value: int, _address: Address):
        daoFund = self.create_interface_score(self._addresses[DAO_FUND], DaoFundInterface)
        daoFund.transferOmm(_value, _address)

    @only_owner
    @external
    def transferFundFromFeeProvider(self, _token: Address, _value: int, _to: Address):
        feeProvider = self.create_interface_score(self._addresses[FEE_PROVIDER], FeeProviderInterface)
        feeProvider.transferFund(_token, _value, _to)

    @external(readonly=True)
    def getVotersCount(self, vote_index: int) -> dict:
        proposal = ProposalDB(var_key=vote_index, db=self.db)
        return {'for_voters': proposal.for_voters_count.get(), 'against_voters': proposal.against_voters_count.get()}

    @external
    @only_owner
    def setVoteDuration(self, duration: int) -> None:
        """
        Sets the vote duration.
        :param duration: number of days a vote will be active once started
        """
        self._vote_duration.set(duration)

    @external(readonly=True)
    def getVoteDuration(self) -> int:
        """
        Returns the vote duration in days.
        """
        return self._vote_duration.get()

    @external
    @only_owner
    def setQuorum(self, quorum: int) -> None:
        """
        Sets the percentage of the total eligible omm which must participate in a vote
        for a vote to be valid.
        :param quorum: percentage of the total eligible omm required for a vote to be valid
        """
        if not 0 < quorum < EXA:
            revert(TAG + f" Quorum must be between 0 and {EXA}.")
        self._quorum.set(quorum)

    @external(readonly=True)
    def getQuorum(self) -> int:
        """
        Returns the percentage of the total eligible omm which must participate in a vote
        for a vote to be valid.
        """
        return self._quorum.get()

    @external
    @only_owner
    def setVoteDefinitionFee(self, fee: int) -> None:
        """
        Sets the fee for defining votes. Fee in Omm.
        """
        self._vote_definition_fee.set(fee)

    @external(readonly=True)
    def getVoteDefinitionFee(self) -> int:
        """
        Returns the Omm fee required for defining a vote.
        """
        return self._vote_definition_fee.get()

    @external
    @only_owner
    def setBoostedOmmVoteDefinitionCriterion(self, _percentage: int) -> None:
        """
        Sets the minimum percentage of boosted OMM tokens which a user must have 
        in order to define a vote.
        :param _percentage: percent represented in basis points
        """
        if not (0 <= _percentage <= EXA):
            revert(TAG + f" Basis point must be between 0 and {EXA}.")
        self._boosted_omm_vote_definition_criterion.set(_percentage)

    @external(readonly=True)
    def getBoostedOmmVoteDefinitionCriterion(self) -> int:
        """
        Returns the minimum percentage of boosted OMM's total supply which a user must have 
        in order to define a vote. Percentage is returned as basis points.
        """
        return self._boosted_omm_vote_definition_criterion.get()

    @external
    def cancelVote(self, vote_index: int) -> None:
        """
        Cancels a vote, in case a mistake was made in its definition.
        """
        proposal = ProposalDB(vote_index, self.db)
        eligible_addresses = [proposal.proposer.get(), self.owner]

        if self.msg.sender not in eligible_addresses:
            revert("Only owner or proposer may call this method.")
        if proposal.start_snapshot.get() <= self.now() and self.msg.sender != self.owner:
            revert("Only owner can cancel a vote that has started.")
        if vote_index < 1 or vote_index > ProposalDB.proposal_count(self.db):
            revert(f"There is no proposal with index {vote_index}.")
        if proposal.status.get() != ProposalStatus.STATUS[ProposalStatus.ACTIVE]:
            revert("Omm Governance: Proposal can be cancelled only from active status.")

        self._refund_vote_definition_fee(proposal)
        proposal.active.set(False)
        proposal.status.set(ProposalStatus.STATUS[ProposalStatus.CANCELLED])

    def _defineVote(self, name: str, description: str, vote_start: int,
                    _proposer: Address, _forum: str) -> None:
        """
        Defines a new vote and which actions are to be executed if it is successful.
        :param name: name of the vote
        :param description: description of the vote
        :param vote_start: timestamp to start the vote
        :param _proposer: the wallet address that created the proposal
        :param _forum: link to the discussion forum 

        """
        if len(description) > 500:
            revert(TAG + f'Description must be less than or equal to 500 characters.')
        snapshot = self.block_height
        current_time = self.now()

        if len(str(current_time)) != len(str(vote_start)):
            revert(TAG + f'vote start timestamp should be in microseconds {current_time}  {vote_start}')

        if vote_start < current_time:
            revert(f'Vote cannot start before the current timestamp.')

        vote_index = ProposalDB.proposal_id(name, self.db)
        if vote_index > 0:
            revert(f'Poll name {name} has already been used.')

        boosted_omm = self.create_interface_score(self._addresses["bOMM"], BoostedOmmInterface)
        user_bomm_balance = boosted_omm.balanceOfAt(_proposer, snapshot)
        bomm_total = boosted_omm.totalSupplyAt(snapshot)
        bomm_criterion = self.getBoostedOmmVoteDefinitionCriterion()

        if (EXA * user_bomm_balance) // bomm_total < bomm_criterion:
            revert(f'User needs at least {100 * bomm_criterion / EXA}% of total bOMM supply to define a vote.')
        proposal = ProposalDB.create_proposal(name=name, description=description, proposer=_proposer,
                                              quorum=self._quorum.get(),
                                              majority=MAJORITY, snapshot=snapshot, start=vote_start,
                                              end=vote_start + self._vote_duration.get(),
                                              fee=self._vote_definition_fee.get(), forum=_forum, db=self.db)
        self.ProposalCreated(proposal.id[name], name, _proposer)

    @external(readonly=True)
    def maxActions(self) -> int:
        return 5

    @external(readonly=True)
    def getProposalCount(self) -> int:
        return ProposalDB.proposal_count(self.db)

    @external(readonly=True)
    def getProposals(self, batch_size: int = 20, offset: int = 1) -> list:
        proposal_list = []
        start = max(1, offset)
        end = min(start + batch_size, self.getProposalCount())
        for proposal_id in range(start, end + 1):
            proposal = self.checkVote(proposal_id)
            proposal_list.append(proposal)
        return proposal_list

    @only_owner
    @external
    def updateVoteForum(self, vote_index: int, forum: str):
        proposal = ProposalDB(var_key=vote_index, db=self.db)
        proposal.forum_link.set(forum)

    @external
    def castVote(self, vote_index: int, vote: bool) -> None:
        """
        Casts a vote in the named poll.
        """
        proposal = ProposalDB(var_key=vote_index, db=self.db)
        start_snap = proposal.start_snapshot.get()
        end_snap = proposal.end_snapshot.get()
        if vote_index <= 0 or not start_snap <= self.now() < end_snap or proposal.active.get() is False:
            revert(f'That is not an active poll.')
        sender = self.msg.sender
        snapshot = proposal.vote_snapshot.get()

        voting_weight = self.myVotingWeight(sender, snapshot)
        if voting_weight == 0:
            revert(f'Boosted OMM tokens needed to cast the vote.')

        prior_vote = (proposal.for_votes_of_user[sender], proposal.against_votes_of_user[sender])
        total_for_votes = proposal.total_for_votes.get()
        total_against_votes = proposal.total_against_votes.get()
        total_for_voters_count = proposal.for_voters_count.get()
        total_against_voters_count = proposal.against_voters_count.get()
        if vote:
            proposal.for_votes_of_user[sender] = voting_weight
            proposal.against_votes_of_user[sender] = 0
            total_for = total_for_votes + voting_weight - prior_vote[0]
            total_against = total_against_votes - prior_vote[1]
            if prior_vote[0] == 0 and prior_vote[1] == 0:
                proposal.for_voters_count.set(total_for_voters_count + 1)
            else:
                if prior_vote[1]:
                    proposal.against_voters_count.set(total_against_voters_count - 1)
                    proposal.for_voters_count.set(total_for_voters_count + 1)
        else:
            proposal.for_votes_of_user[sender] = 0
            proposal.against_votes_of_user[sender] = voting_weight
            total_for = total_for_votes - prior_vote[0]

            total_against = total_against_votes + voting_weight - prior_vote[1]
            if prior_vote[0] == 0 and prior_vote[1] == 0:
                proposal.against_voters_count.set(total_against_voters_count + 1)
            else:
                if prior_vote[0]:
                    proposal.against_voters_count.set(total_against_voters_count + 1)
                    proposal.for_voters_count.set(total_for_voters_count - 1)

        proposal.total_for_votes.set(total_for)
        proposal.total_against_votes.set(total_against)
        self.VoteCast(proposal.name.get(), vote, sender, voting_weight, total_for, total_against)

    def evaluateVote(self, vote_index: int) -> 'ProposalDB':
        """
        Evaluates a vote after the voting period is done. If the vote passed,
        any actions included in the proposal are executed. The vote definition fee
        is also refunded to the proposer if the vote passed.
        """
        proposal = ProposalDB(vote_index, self.db)
        end_snap = proposal.end_snapshot.get()
        majority = proposal.majority.get()

        if vote_index < 1 or vote_index > ProposalDB.proposal_count(self.db):
            revert(f"There is no proposal with index {vote_index}.")
        if self.now() < end_snap:
            revert("Omm Governance: Voting period has not ended.")
        if not proposal.active.get():
            revert("This proposal is not active.")

        result = self.checkVote(vote_index)
        if result['for'] + result['against'] >= result['quorum']:
            if (EXA - majority) * result['for'] > majority * result['against']:
                proposal.status.set(ProposalStatus.STATUS[ProposalStatus.SUCCEEDED])
                self._refund_vote_definition_fee(proposal)
            else:
                proposal.status.set(ProposalStatus.STATUS[ProposalStatus.DEFEATED])
        else:
            proposal.status.set(ProposalStatus.STATUS[ProposalStatus.NO_QUORUM])
        proposal.active.set(False)
        return proposal

    @external
    @only_owner
    def execute_proposal(self, vote_index: int) -> None:
        proposal = self.evaluateVote(vote_index)
        status = proposal.status.get()
        if status == "Succeeded":
            status = ProposalStatus.STATUS[ProposalStatus.EXECUTED]
            proposal.status.set(status)
        self.ActionExecuted(vote_index, status)

    @external
    @only_owner
    def setProposalStatus(self, vote_index: int, _status: str):
        if _status not in ProposalStatus.STATUS:
            revert(TAG + f"invalid status sent")
        proposal = ProposalDB(vote_index, self.db)
        proposal.status.set(_status)

    def _refund_vote_definition_fee(self, proposal: ProposalDB) -> None:
        if not proposal.fee_refunded.get():
            proposal.fee_refunded.set(True)
            self.transferOmmFromDaoFund(proposal.fee.get(), proposal.proposer.get())

    @external(readonly=True)
    def getVoteIndex(self, _name: str) -> int:
        return ProposalDB.proposal_id(_name, self.db)

    @external(readonly=True)
    def checkVote(self, _vote_index: int) -> dict:
        if _vote_index < 1 or _vote_index > ProposalDB.proposal_count(self.db):
            return {}
        vote_data = ProposalDB(_vote_index, self.db)
        try:
            boosted_omm = self.create_interface_score(self._addresses["bOMM"], BoostedOmmInterface)
            total_bomm = boosted_omm.totalSupplyAt(vote_data.vote_snapshot.get())
        except Exception:
            total_bomm = 0
        if total_bomm == 0:
            _for = 0
            _against = 0
        else:
            total_voted = (vote_data.total_for_votes.get(), vote_data.total_against_votes.get())
            _for = EXA * total_voted[0] // total_bomm
            _against = EXA * total_voted[1] // total_bomm

        vote_status = {'id': _vote_index,
                       'name': vote_data.name.get(),
                       'proposer': vote_data.proposer.get(),
                       'description': vote_data.description.get(),
                       'majority': vote_data.majority.get(),
                       'vote snapshot': vote_data.vote_snapshot.get(),
                       'start day': vote_data.start_snapshot.get(),
                       'end day': vote_data.end_snapshot.get(),
                       'quorum': vote_data.quorum.get(),
                       'for': _for,
                       'against': _against,
                       'for_voter_count': vote_data.for_voters_count.get(),
                       'against_voter_count': vote_data.against_voters_count.get(),
                       'forum': vote_data.forum_link.get()
                       }
        status = vote_data.status.get()
        majority = vote_status['majority']
        if status == ProposalStatus.STATUS[ProposalStatus.ACTIVE] and self.now() >= vote_status["end day"]:
            if vote_status['for'] + vote_status['against'] < vote_status['quorum']:
                vote_status['status'] = ProposalStatus.STATUS[ProposalStatus.NO_QUORUM]
            elif (EXA - majority) * vote_status['for'] > majority * vote_status['against']:
                vote_status['status'] = ProposalStatus.STATUS[ProposalStatus.SUCCEEDED]
            else:
                vote_status['status'] = ProposalStatus.STATUS[ProposalStatus.DEFEATED]
        else:
            vote_status['status'] = status

        return vote_status

    @external(readonly=True)
    def getVotesOfUser(self, vote_index: int, user: Address) -> dict:
        vote_data = ProposalDB(vote_index, self.db)
        return {"for": vote_data.for_votes_of_user[user], "against": vote_data.against_votes_of_user[user]}

    @external(readonly=True)
    def myVotingWeight(self, _address: Address, _block: int) -> int:
        boosted_omm = self.create_interface_score(self._addresses["bOMM"], BoostedOmmInterface)
        return boosted_omm.balanceOfAt(_address, _block)

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        vote_fee = self._vote_definition_fee.get()
        if self.msg.sender != self._addresses['ommToken']:
            revert(TAG + "invalid token sent")
        if _value < vote_fee:
            revert(TAG + "insufficient fee sent ")
        try:
            d = json_loads(_data.decode("utf-8"))
            params = d.get("params")
            method = d.get("method")
        except:
            revert(f'{TAG}: Invalid data: {_data}.')
        if method == "defineVote" and params is not None:
            name = params.get("name")
            description = params.get("description")
            vote_start = params.get("vote_start", self.now())
            forum = params.get("forum")
            self._defineVote(name, description, vote_start, _from, forum)
        else:
            revert(f'{TAG}: No valid method called, data: {_data}')

        # transferring omm to daoFund
        omm = self.create_interface_score(self._addresses['ommToken'], OmmTokenInterface)
        omm.transfer(self._addresses['daoFund'], vote_fee)

        # returning extra omm to proposer
        if _value - vote_fee > 0:
            omm.transfer(_from, _value - vote_fee)

    @external
    @only_owner
    def enableHandleActions(self):
        rewards = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        rewards.enableHandleActions()

    @external
    @only_owner
    def disableHandleActions(self):
        rewards = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        rewards.disableHandleActions()
