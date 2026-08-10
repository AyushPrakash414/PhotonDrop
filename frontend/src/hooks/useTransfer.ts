import { useState, useEffect } from 'react';
import { useSender } from './useSender';
import { useReceiver } from './useReceiver';

export function useTransfer() {
  const sender = useSender();
  const receiver = useReceiver();

  const isOpticalLinkActive = sender.senderState.is_transmitting || receiver.receiverState.is_active;

  return {
    sender,
    receiver,
    isOpticalLinkActive,
  };
}
