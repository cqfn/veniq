public class Test2 {

  /**
   * Calls copy();deleteSelected();
   */
  public void cut()
  {
      copy();
      deleteSelected();
  }

  public void copy()
  {
  if (startPosition >= endPosition) return;

  myClipboard.setContents(content, startPosition, endPosition - startPosition);
  }


}
