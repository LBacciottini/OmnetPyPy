from discrete_sim import sim_log


class CongestionController:
    """
    A simple congestion controller that uses the Additive Increase Multiplicative Decrease (AIMD) algorithm
    """
    def __init__(self):

        self.congestion_windows = {}  # dictionary of congestion windows, one for each flow, indexed by flow_id
        self.estimated_rtt = {}
        self.dev_rtt = {}
        self.requests_in_flight = {}  # dictionary of requests in flight, one list for each flow, indexed by flow_id
        # every element in the list is a tuple (req_id, time_sent, timeout)
        self.max_congestion_window = 1000  # maximum congestion window size
        self.consecutive_acks = {}  # dictionary of consecutive acks, one for each flow, indexed by flow_id
        self.consecutive_acks_required = 1  # number of consecutive acks to receive before increasing the congestion window

        self.other_ends = {}  # dictionary of other end identifiers, one for each flow, indexed by flow_id

    def halve_congestion_window(self, flow_id):
        """
        Halve the congestion window for the given flow
        """
        self.congestion_windows[flow_id] = max(1, self.congestion_windows[flow_id] // 2)

    def increase_congestion_window(self, flow_id):
        """
        Increase the congestion window for the given flow
        """
        self.congestion_windows[flow_id] = min(self.max_congestion_window, self.congestion_windows[flow_id] +
                                               self.consecutive_acks_required)

    def setup_congestion_control(self, flow):
        """
        Setup the congestion control variables for the given flow
        """
        self.congestion_windows[flow["flow_id"]] = 2  # initial congestion window size
        self.estimated_rtt[flow["flow_id"]] = 30 * (len(flow["path"]) - 1) * 10  # 300 us per hop is the initial value
        self.dev_rtt[flow["flow_id"]] = 0.05 * self.estimated_rtt[flow["flow_id"]]  # 5% of the estimated RTT
        self.requests_in_flight[flow["flow_id"]] = []
        self.other_ends[flow["flow_id"]] = flow["destination"]
        self.consecutive_acks[flow["flow_id"]] = 0  # number of consecutive acks to receive before increasing the congestion window

    def collect_timeouts(self, current_time):
        """
        Collect the timeouts for the requests in flight and update the congestion windows for the involved flows
        """
        for flow_id in self.requests_in_flight:
            timed_out = False
            requests = self.requests_in_flight[flow_id]
            new_requests = []
            for req_id, time_sent, timeout in requests:
                if current_time - time_sent > timeout:
                    # the request has timed out
                    # we have to halve the congestion window
                    timed_out = True
                else:
                    new_requests.append((req_id, time_sent, timeout))
            self.requests_in_flight[flow_id] = new_requests
            if timed_out:
                """
                sim_log.debug(
                f"Flow {flow_id} timed out, halving congestion window {self.congestion_windows[flow_id]}")
                """
                self.halve_congestion_window(flow_id)

    def handle_ack(self, flow_id, req_id, current_time, mark_congested=False):
        """
        Handle the ACK for the given request

        Parameters
        ----------
        flow_id : int
            The flow id
        req_id : int
            The request id
        current_time : float
            The current time
        mark_congested : bool, optional
            Whether the ack was marked as congested or not

        Returns
        -------
        int
            The number of new requests to generate for the flow
        """
        num_skipped = 0

        found = False
        for req, time_sent, timeout in self.requests_in_flight[flow_id]:
            if req < req_id:
                num_skipped += 1
                # if we receive an ACK for a request, we can remove all the requests with lower req_id
                # because they have been surely dropped due to congestion
            elif req == req_id:
                # we found the request for which we received the ACK
                # remove it from the list
                found = True

                # update the estimated RTT
                sample_rtt = current_time - time_sent
                self.estimated_rtt[flow_id] = 0.875 * self.estimated_rtt[flow_id] + 0.125 * sample_rtt
                self.dev_rtt[flow_id] = 0.75 * self.dev_rtt[flow_id] + 0.25 * abs(sample_rtt - self.estimated_rtt[flow_id])
                # print(f"Estimated RTT for flow {flow_id} is {self.estimated_rtt[flow_id]}, dev RTT is {self.dev_rtt[flow_id]}")

        if found:
            # remove the tuples from the list
            self.requests_in_flight[flow_id] = self.requests_in_flight[flow_id][num_skipped + 1:]

        else:
            self.requests_in_flight[flow_id] = self.requests_in_flight[flow_id][num_skipped:]

        # for _ in range(num_skipped):
        if num_skipped > 0:
            self.halve_congestion_window(flow_id)

        if mark_congested:
            self.halve_congestion_window(flow_id)

        if num_skipped > 0 or mark_congested:
            self.consecutive_acks[flow_id] = 0

        # we increase the congestion window
        if found:
            self.consecutive_acks[flow_id] += 1
        if self.consecutive_acks[flow_id] == self.consecutive_acks_required:
            self.increase_congestion_window(flow_id)
            self.consecutive_acks[flow_id] = 0

        # return the number of new requests to generate
        return max(self.congestion_windows[flow_id] - len(self.requests_in_flight[flow_id]), 0)

    def handle_new_request_in_flight(self, flow_id, req_id, current_time):
        """
        Handle a new request in flight for the given flow
        """
        timeout = max(self.estimated_rtt[flow_id] + 4 * self.dev_rtt[flow_id], 0.1)
        self.requests_in_flight[flow_id].append((req_id, current_time, timeout))

    def get_congestion_window(self, flow_id):
        """
        Get the congestion window for the given flow

        Returns
        -------
        int
            The congestion window size
        """
        return self.congestion_windows[flow_id]