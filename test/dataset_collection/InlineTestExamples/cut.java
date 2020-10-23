public class Test2 {

  /**
   * Calls copy();deleteSelected();
   */
  public void cut()
  {
      if (startPosition >= endPosition) return;
     
      myClipboard.setContents(content, startPosition, endPosition - startPosition);
      deleteSelected();
  }

  public void copy()
  {
  if (startPosition >= endPosition) return;

  myClipboard.setContents(content, startPosition, endPosition - startPosition);
  }


}
